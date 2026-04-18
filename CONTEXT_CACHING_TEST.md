# Gemini Context Caching Test

## Overview

This test demonstrates **Gemini's context caching** feature with Agno, which dramatically reduces API costs and latency by caching large system prompts.

## What is Context Caching?

Context caching allows you to cache static content (like system prompts) so it doesn't need to be sent with every request. This is particularly valuable when using large system prompts (like our comprehensive medical AI prompts which are 50,000+ characters).

### Key Benefits:

- **Cost Reduction**: Cached tokens are much cheaper than regular input tokens
- **Faster Responses**: Reduced data transfer = faster API calls
- **Efficiency**: Perfect for repetitive contexts (system prompts, knowledge bases)

## Our Implementation

### What Gets Cached:

- **Full system prompt** from `config/prompts.py` (~50,000 characters)
- Includes:
  - Base medical AI instructions
  - Session state management guide
  - Long-form content generation instructions
  - Markdown/LaTeX formatting rules
  - Few-shot examples

### Cache Configuration:

```python
MODEL_ID = "gemini-2.0-flash-001"
CACHE_TTL = "30s"  # 30 seconds (configurable)
```

### How It Works:

```
┌─────────────────────────────────────────────────────────┐
│                   FIRST REQUEST                         │
├─────────────────────────────────────────────────────────┤
│  1. Check if cache exists: ❌ NO                        │
│  2. Create cache with system prompt                     │
│  3. Store cache name in cache_name.txt                  │
│  4. Run agent with cached_content=cache.name            │
│  5. Cache expires in 30 seconds                         │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│                SUBSEQUENT REQUESTS (within 30s)         │
├─────────────────────────────────────────────────────────┤
│  1. Check if cache exists: ✅ YES                       │
│  2. Validate cache hasn't expired                       │
│  3. Reuse existing cache (CACHE HIT)                    │
│  4. Run agent with cached_content=cache.name            │
│  5. 💰 Save ~12,500 tokens per request!                │
└─────────────────────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────────────────────┐
│              AFTER 30 SECONDS (cache expired)           │
├─────────────────────────────────────────────────────────┤
│  1. Check if cache exists: ⚠️  EXPIRED                  │
│  2. Create NEW cache with system prompt                 │
│  3. Update cache_name.txt                               │
│  4. Run agent with new cached_content                   │
│  5. New cache expires in 30 seconds                     │
└─────────────────────────────────────────────────────────┘
```

## Usage

### Prerequisites:

```bash
# Install dependencies
pip install agno google-genai python-dotenv

# Set API key
export GOOGLE_API_KEY=your_api_key_here
# or add to .env file
```

### Run the Test:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run test
python test_gemini_context_caching.py
```

## Test Scenarios

### Test 1: Basic Cache Functionality
- Creates cache with full system prompt
- Makes first request (cache miss)
- Shows cache creation details

### Test 2: Cache Reuse
- Makes immediate second request
- Demonstrates cache hit
- Shows token savings

### Test 3: Cache Expiration (Optional)
- Uncomment `test_cache_expiration()` in main()
- Waits 31 seconds for cache to expire
- Demonstrates cache recreation

## Expected Output

```
================================================================================
🚀 GEMINI CONTEXT CACHING TEST
================================================================================
📅 Timestamp: 2026-01-12 15:30:00
🤖 Model: gemini-2.0-flash-001
⏰ Cache TTL: 30s
📋 System Prompt: Loaded from config/prompts.py

================================================================================
🔍 CHECKING CACHE STATUS
================================================================================
❌ No existing cache found

--------------------------------------------------------------------------------
🔨 CACHE MISS - Creating new cache
--------------------------------------------------------------------------------
✅ Cache created successfully
📝 Cache name: cachedContents/xyz123abc
⏰ Cache expires at: 2026-01-12T15:30:30Z
📊 System prompt size: 52341 characters
📊 Estimated cached tokens: ~13085

================================================================================
🤖 TESTING AGENT WITH CACHED CONTEXT
================================================================================
Query: What is preeclampsia? Provide a brief 100-word summary.
--------------------------------------------------------------------------------

📤 Response:
Preeclampsia is a pregnancy-specific multisystem disorder characterized by new-onset 
hypertension (≥140/90 mmHg) after 20 weeks' gestation, accompanied by proteinuria or 
evidence of end-organ dysfunction...

📊 Metrics:
  • Response time: 2.34s
  • Input tokens: 156
  • Output tokens: 124
  • Total tokens: 280
  • Cache read tokens: 13085

================================================================================
TEST 2: CACHE REUSE (IMMEDIATE REQUEST)
================================================================================
📄 Found stored cache name: cachedContents/xyz123abc
⏰ Cache expires at: 2026-01-12T15:30:30Z
✅ CACHE HIT - Reusing existing cache
💰 Token savings: 13085 tokens

================================================================================
✅ ALL TESTS COMPLETED SUCCESSFULLY
================================================================================

💡 KEY OBSERVATIONS:
  • First request creates cache (slower, no cache savings)
  • Subsequent requests reuse cache (faster, significant token savings)
  • System prompt is ~50,000+ characters = ~12,500+ tokens saved per request
  • Cache expires after 30 seconds (configurable with CACHE_TTL)

🧹 Cleaned up cache name file
```

## Token Savings Calculation

### Without Caching (per request):
- System prompt: ~13,085 tokens
- User query: ~50 tokens
- **Total input: ~13,135 tokens**

### With Caching (per request after first):
- Cached system prompt: 0 tokens sent (read from cache)
- User query: ~50 tokens
- **Total input: ~50 tokens**

### Savings Per Request:
- **~13,085 tokens saved (99.6% reduction in input tokens!)**
- **Cost savings**: Cached tokens are significantly cheaper

## Configuration Options

### Adjust Cache TTL:

```python
# In test_gemini_context_caching.py
CACHE_TTL = "300s"  # 5 minutes
CACHE_TTL = "3600s"  # 1 hour
CACHE_TTL = "86400s"  # 24 hours (max for Gemini)
```

### Use Different Model:

```python
MODEL_ID = "gemini-2.0-flash-exp"  # Experimental
MODEL_ID = "gemini-2.0-pro-001"    # Pro version
```

### Modify System Prompt:

The test automatically loads the full system prompt from `config/prompts.py` using:

```python
from config.prompts import load_system_prompt
system_prompt = load_system_prompt()
```

Any changes to prompts in `config/prompts.py` will be reflected in the cache.

## Important Notes

### Cache Persistence:
- Cache name is stored in `cache_name.txt` to enable reuse across script runs
- File is automatically cleaned up after tests
- In production, you might store this in a database or environment variable

### Cache Limits:
- Minimum content size: 32,768 tokens
- Maximum TTL: 24 hours
- See [Google's documentation](https://ai.google.dev/gemini-api/docs/caching?lang=python) for details

### Cost Considerations:
- **Cache storage**: Small cost per hour (very cheap)
- **Cache reads**: ~90% cheaper than regular input tokens
- **Break-even**: After ~2-3 requests, caching pays for itself

### When to Use Caching:
✅ **Good for:**
- Large, static system prompts
- Repeated queries with same context
- Production agents with fixed instructions
- Knowledge base content

❌ **Not ideal for:**
- Rapidly changing context
- Single-use prompts
- Small prompts (< 32k tokens)

## Integration with Medical Bot

To use caching in the main Medical Bot (`app.py`):

```python
from google import genai
from config.prompts import load_system_prompt

# Create cache once at startup
client = genai.Client()
system_prompt = load_system_prompt()

cache = client.caches.create(
    model="gemini-2.0-flash-001",
    config={
        "system_instruction": system_prompt,
        "ttl": "3600s",  # 1 hour
    },
)

# Use in agent
agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash-001",
        cached_content=cache.name,  # ← Use cached content
        temperature=0.3,
    ),
    # ... other config
)
```

### Cache Refresh Strategy:

```python
def get_or_refresh_cache(client, cache_name, system_prompt, ttl="3600s"):
    """
    Get existing cache or create/refresh if expired.
    """
    try:
        cache = client.caches.get(name=cache_name)
        if cache.expire_time:  # Still valid
            return cache
    except:
        pass
    
    # Create new cache
    return client.caches.create(
        model="gemini-2.0-flash-001",
        config={"system_instruction": system_prompt, "ttl": ttl}
    )
```

## Monitoring Cache Performance

The test outputs detailed metrics:

- **Cache creation time**: How long to create cache
- **Response time**: Request latency
- **Token counts**: Input, output, cached tokens
- **Cache status**: Hit/miss indication

Track these metrics in production to:
- Measure cost savings
- Optimize cache TTL
- Identify cache inefficiencies

## References

- [Google Gemini Context Caching](https://ai.google.dev/gemini-api/docs/caching?lang=python)
- [Agno Gemini Integration](https://docs.agno.com/integrations/models/native/google/overview)
- [Agno Context Management](https://docs.agno.com/basics/context/overview)

## Troubleshooting

### "Cache not found" error:
- Cache may have expired
- Check `cache_name.txt` exists
- Verify API key has caching permissions

### "Content too small" error:
- Minimum 32,768 tokens required
- Our system prompt meets this requirement
- Don't use caching for small prompts

### Slow first request:
- Normal - cache creation takes time
- Subsequent requests will be faster
- Consider pre-warming cache at startup

## License

MIT License - Part of Medical Bot v3 Project
