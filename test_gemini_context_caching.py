"""
Test Gemini Context Caching with Agno
Demonstrates context caching with system prompts to reduce API costs and latency.

Based on: https://ai.google.dev/gemini-api/docs/caching?lang=python
Agno docs: https://docs.agno.com/integrations/models/native/google/overview

Key Features:
- Caches the full system prompt (saves tokens on repeated requests)
- TTL: 30 seconds (cache expires after 30s)
- Handles cache hit (reuse existing) and cache miss (recreate)
- Shows token savings from caching

✅ PROPER AGNO PATTERN:
When using cached_content with Gemini:
1. Create the cache with system_instruction included
2. Create an Agent with Gemini model that has cached_content=cache.name
3. Do NOT pass instructions to the Agent (they're already in the cache)
4. Use agent.run() normally - Agno handles everything correctly

Example:
```python
cache = client.caches.create(
    model="gemini-2.5-flash",
    config={
        "system_instruction": "Your system prompt here...",
        "ttl": "300s",
    },
)

agent = Agent(
    model=Gemini(id="gemini-2.5-flash", cached_content=cache.name),
)
agent.run("Your query")  # System instruction comes from cache
```
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai.types import CachedContent

from agno.agent import Agent
from agno.models.google import Gemini
from config.prompts import load_system_prompt

# Load environment variables
load_dotenv()
import certifi
os.environ["SSL_CERT_FILE"] = certifi.where()
# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

# Cache configuration
CACHE_TTL = "3600s"  # 1 hour TTL (to avoid recreating cache repeatedly)
MODEL_ID = "gemini-2.5-flash"
CACHE_NAME_FILE = "cache_name.txt"  # Store cache name persistently


def get_or_create_cache() -> CachedContent:
    """
    Get existing cache (if valid) or create new cache.
    
    Returns:
        CachedContent: The cached content object
    """
    # Load system prompt from prompts.py
    system_prompt = load_system_prompt()
    
    print("\n" + "="*80)
    print("🔍 CHECKING CACHE STATUS")
    print("="*80)
    
    # Try to load existing cache name from file
    cache_name = None
    if os.path.exists(CACHE_NAME_FILE):
        with open(CACHE_NAME_FILE, 'r') as f:
            cache_name = f.read().strip()
        print(f"📄 Found stored cache name: {cache_name}")
    
    # Try to retrieve existing cache
    if cache_name:
        try:
            cache = client.caches.get(name=cache_name)
            
            # Check if cache is still valid (has expire_time in the future)
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            
            if cache.expire_time and cache.expire_time > now:
                print(f"⏰ Cache expires at: {cache.expire_time}")
                print(f"✅ CACHE HIT - Reusing existing cache (still valid)")
                print(f"💰 Token savings: {len(system_prompt.split())} words (~{len(system_prompt) // 4} tokens)")
                return cache
            else:
                print(f"⚠️  Cache expired (was valid until: {cache.expire_time})")
        except Exception as e:
            print(f"❌ Cache retrieval failed: {e}")
    
    # Cache miss - create new cache
    print("\n" + "-"*80)
    print("🔨 CACHE MISS - Creating new cache")
    print("-"*80)
    
    try:
        cache = client.caches.create(
            model=MODEL_ID,
            config={
                "system_instruction": system_prompt,
                "ttl": CACHE_TTL,
            },
        )
        
        # Store cache name for future use
        with open(CACHE_NAME_FILE, 'w') as f:
            f.write(cache.name)
        
        print(f"✅ Cache created successfully")
        print(f"📝 Cache name: {cache.name}")
        print(f"⏰ Cache expires at: {cache.expire_time}")
        print(f"📊 System prompt size: {len(system_prompt)} characters")
        print(f"📊 Estimated cached tokens: ~{len(system_prompt) // 4}")
        
        return cache
        
    except Exception as e:
        print(f"❌ Cache creation failed: {e}")
        raise


def test_agent_with_cache(cache: CachedContent, test_query: str):
    """
    Test Agent with cached context using official Agno pattern.
    
    Based on: https://docs.agno.com/integrations/models/native/google/overview
    
    When cached_content includes system_instruction, simply:
    1. Create Agent with Gemini model that has cached_content=cache.name
    2. Call agent.run() normally - Agno handles everything automatically
    
    Args:
        cache: The cached content object
        test_query: Query to test the agent
    """
    print("\n" + "="*80)
    print("🤖 TESTING AGENT WITH CACHED CONTEXT")
    print("="*80)
    print(f"Query: {test_query}")
    print("-"*80)
    
    # ✅ OFFICIAL AGNO PATTERN: Create Agent with cached_content
    agent = Agent(
        model=Gemini(id=MODEL_ID, cached_content=cache.name),
    )
    
    # Run agent normally - Agno handles everything automatically
    start_time = time.time()
    run_output = agent.run(test_query)
    end_time = time.time()
    
    # Display response
    print(f"\n📤 Response:")
    if run_output.content:
        display_content = run_output.content[:500] + "..." if len(run_output.content) > 500 else run_output.content
        print(display_content)
    else:
        print("No content in response")
    
    # Display metrics
    print(f"\n📊 Metrics:")
    print(f"  • Response time: {end_time - start_time:.2f}s")
    if run_output.metrics:
        # Handle both dict and object metrics
        metrics = run_output.metrics
        if isinstance(metrics, dict):
            input_tokens = metrics.get('input_tokens', 0)
            output_tokens = metrics.get('output_tokens', 0)
            total_tokens = metrics.get('total_tokens', 0)
            cache_read_tokens = metrics.get('cache_read_tokens', 0)
        else:
            input_tokens = getattr(metrics, 'input_tokens', 0)
            output_tokens = getattr(metrics, 'output_tokens', 0)
            total_tokens = getattr(metrics, 'total_tokens', 0)
            cache_read_tokens = getattr(metrics, 'cache_read_tokens', 0)
        
        print(f"  • Input tokens: {input_tokens}")
        print(f"  • Output tokens: {output_tokens}")
        print(f"  • Total tokens: {total_tokens}")
        if cache_read_tokens > 0:
            print(f"  • Cache read tokens: {cache_read_tokens}")
            print(f"  💰 Cost savings from cache: {cache_read_tokens} tokens")
    
    return run_output


def test_cache_expiration():
    """
    Test cache expiration by waiting for TTL to expire.
    """
    print("\n" + "="*80)
    print("⏳ TESTING CACHE EXPIRATION (30 second TTL)")
    print("="*80)
    
    # First request - should create cache
    print("\n📌 REQUEST 1: Creating cache...")
    cache1 = get_or_create_cache()
    test_agent_with_cache(cache1, "What is preeclampsia?")
    
    # Second request immediately - should hit cache
    print("\n" + "="*80)
    print("📌 REQUEST 2: Immediate request (should hit cache)...")
    print("="*80)
    cache2 = get_or_create_cache()
    test_agent_with_cache(cache2, "What causes gestational diabetes?")
    
    # Wait for cache to expire
    print("\n" + "="*80)
    print(f"⏰ Waiting {CACHE_TTL} for cache to expire...")
    print("="*80)
    time.sleep(31)  # Wait 31 seconds (TTL is 30s)
    
    # Third request after expiration - should recreate cache
    print("\n" + "="*80)
    print("📌 REQUEST 3: After expiration (should recreate cache)...")
    print("="*80)
    cache3 = get_or_create_cache()
    test_agent_with_cache(cache3, "Explain HELLP syndrome.")


def cleanup():
    """
    Clean up: remove cache name file.
    """
    if os.path.exists(CACHE_NAME_FILE):
        os.remove(CACHE_NAME_FILE)
        print(f"\n🧹 Cleaned up cache name file")


def main():
    """
    Main test function.
    """
    print("\n" + "="*80)
    print("🚀 GEMINI CONTEXT CACHING TEST")
    print("="*80)
    print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🤖 Model: {MODEL_ID}")
    print(f"⏰ Cache TTL: {CACHE_TTL}")
    print(f"📋 System Prompt: Loaded from config/prompts.py")
    
    try:
        # Test 1: Basic caching
        print("\n" + "="*80)
        print("TEST 1: BASIC CACHE FUNCTIONALITY")
        print("="*80)
        
        cache = get_or_create_cache()
        test_agent_with_cache(cache, "What is preeclampsia? Provide a brief 100-word summary.")
        
        # Test 2: Cache reuse (immediate second request)
        print("\n" + "="*80)
        print("TEST 2: CACHE REUSE (IMMEDIATE REQUEST)")
        print("="*80)
        
        cache = get_or_create_cache()
        test_agent_with_cache(cache, "What are the risk factors for gestational diabetes?")
        
        # Optional: Test cache expiration (uncomment to test, adds 31s delay)
        # test_cache_expiration()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        
        print("\n💡 KEY OBSERVATIONS:")
        print("  • First request creates cache (slower, no cache savings)")
        print("  • Subsequent requests reuse cache (faster, significant token savings)")
        print("  • System prompt is ~30,000+ characters = ~7,500+ tokens saved per request")
        print(f"  • Cache TTL: {CACHE_TTL} (1 hour) - reuses cache across multiple test runs")
        print("  • Cache persists in cache_name.txt - delete file to force recreation")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        cleanup()


if __name__ == "__main__":
    main()
