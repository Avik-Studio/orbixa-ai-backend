# Token Usage Guide - Gemini & Agno Integration

## Overview

This guide explains how to retrieve and track token usage for the Medical Bot Agent OS using both:
1. **Google Gemini API** - Token usage from the model provider
2. **Agno Framework** - Comprehensive metrics including token usage

---

## 1. Gemini API Token Usage

### How Gemini Calculates Tokens

From Google's documentation:
- **1 token ≈ 4 characters**
- **100 tokens ≈ 60-80 English words**
- **Context Window**: Gemini 2.0 Flash has:
  - Input limit: ~1,000,000 tokens
  - Output limit: ~8,000 tokens

### Token Rates for Different Modalities

| Type | Token Rate |
|------|-----------|
| Text | ~4 characters per token |
| Images (≤384px) | 258 tokens fixed |
| Images (>384px) | 258 tokens per 768x768 tile |
| Video | 263 tokens/second |
| Audio | 32 tokens/second |

### Getting Token Usage from Gemini Responses

When you call the Gemini API, the response includes `usage_metadata`:

```python
from google import genai

client = genai.Client()

# Generate content
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="What are the symptoms of diabetes?"
)

# Access token usage
print(response.usage_metadata)
# Output:
# prompt_token_count: 11
# candidates_token_count: 73
# total_token_count: 84
```

### Token Usage Fields in Gemini Response

```python
usage_metadata = {
    "prompt_token_count": 11,        # Input tokens
    "candidates_token_count": 73,    # Output tokens
    "total_token_count": 84          # Total = input + output
}
```

### Pre-counting Tokens (Before API Call)

You can count tokens before making the actual API call:

```python
from google import genai

client = genai.Client()

prompt = "Write a comprehensive guide on hypertension management"

# Count tokens before sending
total_tokens = client.models.count_tokens(
    model="gemini-2.0-flash",
    contents=prompt
)

print("Estimated tokens:", total_tokens)
# Output: total_tokens: 8
```

---

## 2. Agno Framework Token Usage & Metrics

### Overview

Agno automatically tracks token usage at multiple levels:
- **Per Message** - Each message (user, assistant, tool) has metrics
- **Per Run** - Each `RunOutput` has aggregated metrics
- **Per Session** - Session aggregates all run metrics

### RunOutput Metrics Schema

When you run an agent with Agno, the `RunOutput` object contains a `metrics` attribute:

```python
from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-3-flash-preview"),
    instructions="You are a medical assistant"
)

response = agent.run("What is hypertension?")

# Access metrics
print(response.metrics)
```

### Available Metrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `input_tokens` | int | Tokens sent to the model (prompt) |
| `output_tokens` | int | Tokens received from model (response) |
| `total_tokens` | int | Sum of input + output tokens |
| `audio_input_tokens` | int | Audio input tokens (if applicable) |
| `audio_output_tokens` | int | Audio output tokens (if applicable) |
| `audio_total_tokens` | int | Total audio tokens |
| `cache_read_tokens` | int | Tokens read from cache |
| `cache_write_tokens` | int | Tokens written to cache |
| `reasoning_tokens` | int | Tokens used for reasoning (o1 models) |
| `duration` | float | Duration of run in seconds |
| `time_to_first_token` | float | Time until first token generated |
| `provider_metrics` | dict | Provider-specific metrics (Gemini data) |

### Example: Accessing Token Usage

```python
from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(
        id="gemini-3-flash-preview",
        api_key="YOUR_GOOGLE_API_KEY"
    )
)

response = agent.run("Explain Type 2 diabetes pathophysiology")

# Access token metrics
print(f"Input tokens: {response.metrics.input_tokens}")
print(f"Output tokens: {response.metrics.output_tokens}")
print(f"Total tokens: {response.metrics.total_tokens}")
print(f"Duration: {response.metrics.duration}s")

# Provider-specific metrics (Gemini's raw data)
print(f"Provider metrics: {response.metrics.provider_metrics}")
```

### Output Example

```
Input tokens: 45
Output tokens: 250
Total tokens: 295
Duration: 3.2s
Provider metrics: {
    'prompt_token_count': 45,
    'candidates_token_count': 250,
    'total_token_count': 295
}
```

---

## 3. Medical Bot Implementation

### Current Agent Configuration

Your Medical Bot uses Gemini through Agno:

```python
# From agents/medical_agent.py
agent = Agent(
    model=Gemini(
        id=os.getenv("GEMINI_MODEL_ID", "gemini-3-flash-preview"),
        api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        top_p=0.8,
    ),
    # ... other config
)
```

### How to Track Token Usage in Your Medical Bot

#### Option 1: Direct Access in Client Test

Update your `test_agno_client.py` to extract metrics:

```python
async def test_run_agent_simple(self):
    """Test: Run agent with token usage tracking."""
    print("\n" + "-" * 80)
    print("TEST 4: Run Agent with Token Metrics")
    print("-" * 80)
    
    message = "What is hypertension and its main causes?"
    print(f"📧 Sending: '{message}'")
    
    response = await self.client.run_agent(
        agent_id=self.agent_id,
        message=message,
        user_id=self.user_id
    )
    
    print(f"\n✅ Agent responded successfully")
    print(f"   Session ID: {response.session_id if hasattr(response, 'session_id') else 'N/A'}")
    print(f"   Run ID: {response.run_id if hasattr(response, 'run_id') else 'N/A'}")
    
    # ✨ ACCESS TOKEN METRICS
    if hasattr(response, 'metrics'):
        metrics = response.metrics
        print(f"\n📊 Token Usage Metrics:")
        print(f"   Input tokens: {metrics.input_tokens if hasattr(metrics, 'input_tokens') else 'N/A'}")
        print(f"   Output tokens: {metrics.output_tokens if hasattr(metrics, 'output_tokens') else 'N/A'}")
        print(f"   Total tokens: {metrics.total_tokens if hasattr(metrics, 'total_tokens') else 'N/A'}")
        print(f"   Duration: {metrics.duration if hasattr(metrics, 'duration') else 'N/A'}s")
        
        # Provider-specific (Gemini raw data)
        if hasattr(metrics, 'provider_metrics') and metrics.provider_metrics:
            print(f"\n📈 Gemini Provider Metrics:")
            print(f"   {metrics.provider_metrics}")
```

#### Option 2: Session-Level Metrics

Track cumulative token usage across a session:

```python
async def test_get_session_metrics(self):
    """Test: Get cumulative session metrics."""
    if not self.session_id:
        print("⏭️  Skipped (no session ID)")
        return
    
    print("\n" + "-" * 80)
    print("TEST: Get Session Metrics")
    print("-" * 80)
    
    session = await self.client.get_session(
        session_id=self.session_id,
        user_id=self.user_id
    )
    
    # Access session-level aggregated metrics
    if hasattr(session, 'session_metrics'):
        metrics = session.session_metrics
        print(f"\n📊 Cumulative Session Metrics:")
        print(f"   Total input tokens: {metrics.input_tokens if hasattr(metrics, 'input_tokens') else 'N/A'}")
        print(f"   Total output tokens: {metrics.output_tokens if hasattr(metrics, 'output_tokens') else 'N/A'}")
        print(f"   Total tokens: {metrics.total_tokens if hasattr(metrics, 'total_tokens') else 'N/A'}")
        print(f"   Total duration: {metrics.duration if hasattr(metrics, 'duration') else 'N/A'}s")
```

#### Option 3: Per-Message Metrics

Track tokens for each message in the conversation:

```python
# Access message-level metrics
if hasattr(response, 'messages'):
    for idx, message in enumerate(response.messages):
        if hasattr(message, 'metrics') and message.metrics:
            print(f"\nMessage {idx + 1} Metrics:")
            print(f"  Role: {message.role}")
            print(f"  Input tokens: {message.metrics.input_tokens}")
            print(f"  Output tokens: {message.metrics.output_tokens}")
            print(f"  Total tokens: {message.metrics.total_tokens}")
```

---

## 4. Complete Test Example with Token Tracking

Here's a complete test function with comprehensive token tracking:

```python
async def test_token_usage_comprehensive(self):
    """Test: Comprehensive token usage tracking."""
    print("\n" + "=" * 80)
    print("  COMPREHENSIVE TOKEN USAGE TEST")
    print("=" * 80)
    
    # Test 1: Simple query
    print("\n--- Test 1: Simple Medical Query ---")
    response1 = await self.client.run_agent(
        agent_id=self.agent_id,
        message="What is diabetes?",
        user_id=self.user_id
    )
    
    if hasattr(response1, 'metrics'):
        m1 = response1.metrics
        print(f"Query: 'What is diabetes?'")
        print(f"  Input:  {m1.input_tokens} tokens")
        print(f"  Output: {m1.output_tokens} tokens")
        print(f"  Total:  {m1.total_tokens} tokens")
        print(f"  Cost estimate (Gemini 2.0 Flash): ${(m1.input_tokens * 0.075 + m1.output_tokens * 0.30) / 1_000_000:.6f}")
    
    # Test 2: Complex query with knowledge base
    print("\n--- Test 2: Complex Query (with Knowledge Base) ---")
    response2 = await self.client.run_agent(
        agent_id=self.agent_id,
        message="Compare Type 1 and Type 2 diabetes pathophysiology, treatment, and prognosis. Search Harrison's if needed.",
        session_id=response1.session_id if hasattr(response1, 'session_id') else None,
        user_id=self.user_id
    )
    
    if hasattr(response2, 'metrics'):
        m2 = response2.metrics
        print(f"Complex query with knowledge base search")
        print(f"  Input:  {m2.input_tokens} tokens")
        print(f"  Output: {m2.output_tokens} tokens")
        print(f"  Total:  {m2.total_tokens} tokens")
        print(f"  Duration: {m2.duration}s")
    
    # Test 3: Session aggregate
    print("\n--- Test 3: Session Aggregate Metrics ---")
    if hasattr(response1, 'session_id'):
        session = await self.client.get_session(
            session_id=response1.session_id,
            user_id=self.user_id
        )
        
        if hasattr(session, 'session_metrics'):
            sm = session.session_metrics
            print(f"Cumulative session metrics (2 queries):")
            print(f"  Total input:  {sm.input_tokens} tokens")
            print(f"  Total output: {sm.output_tokens} tokens")
            print(f"  Grand total:  {sm.total_tokens} tokens")
            print(f"  Total cost:   ${(sm.input_tokens * 0.075 + sm.output_tokens * 0.30) / 1_000_000:.6f}")
```

---

## 5. Cost Calculation

### Gemini 2.0 Flash Pricing (as of Jan 2026)

| Token Type | Price per 1M tokens |
|------------|---------------------|
| Input tokens (prompt) | $0.075 |
| Output tokens (response) | $0.30 |
| Cached input tokens | $0.01875 |

### Calculate Cost from Metrics

```python
def calculate_cost(metrics):
    """Calculate cost based on Gemini 2.0 Flash pricing."""
    input_cost = (metrics.input_tokens * 0.075) / 1_000_000
    output_cost = (metrics.output_tokens * 0.30) / 1_000_000
    cache_savings = 0
    
    if hasattr(metrics, 'cache_read_tokens') and metrics.cache_read_tokens:
        # Cached tokens are 75% cheaper
        cache_savings = (metrics.cache_read_tokens * 0.075 * 0.75) / 1_000_000
    
    total_cost = input_cost + output_cost - cache_savings
    
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "cache_savings": cache_savings,
        "total_cost": total_cost
    }

# Usage
cost = calculate_cost(response.metrics)
print(f"Cost breakdown:")
print(f"  Input: ${cost['input_cost']:.6f}")
print(f"  Output: ${cost['output_cost']:.6f}")
print(f"  Cache savings: ${cost['cache_savings']:.6f}")
print(f"  Total: ${cost['total_cost']:.6f}")
```

---

## 6. Tracking Token Usage in Production

### Option 1: Log Metrics to Database

```python
# In app.py or agent handler
def log_token_usage(response, user_id, session_id):
    """Log token usage to analytics database."""
    if hasattr(response, 'metrics'):
        metrics = response.metrics
        
        # Save to analytics DB
        analytics_db.insert({
            "timestamp": datetime.now(),
            "user_id": user_id,
            "session_id": session_id,
            "run_id": response.run_id,
            "input_tokens": metrics.input_tokens,
            "output_tokens": metrics.output_tokens,
            "total_tokens": metrics.total_tokens,
            "duration": metrics.duration,
            "cost": calculate_cost(metrics)["total_cost"]
        })
```

### Option 2: Real-time Monitoring Dashboard

Track metrics in real-time:

```python
# Create endpoint for metrics dashboard
@app.get("/metrics/usage")
async def get_usage_metrics(
    user_id: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """Get token usage metrics for analytics."""
    
    # Query MongoDB for sessions
    sessions = db.sessions.find({
        "user_id": user_id,
        "created_at": {"$gte": start_date, "$lte": end_date}
    })
    
    total_tokens = 0
    total_cost = 0
    
    for session in sessions:
        if "session_metrics" in session:
            total_tokens += session["session_metrics"]["total_tokens"]
            total_cost += calculate_cost(session["session_metrics"])["total_cost"]
    
    return {
        "user_id": user_id,
        "period": {"start": start_date, "end": end_date},
        "total_tokens": total_tokens,
        "estimated_cost": total_cost,
        "sessions_count": len(list(sessions))
    }
```

---

## 7. Summary: Key Takeaways

### Getting Token Usage - Quick Reference

1. **Per Run**:
   ```python
   response = await client.run_agent(agent_id="medical-agent", message="...")
   tokens = response.metrics.total_tokens
   ```

2. **Per Session**:
   ```python
   session = await client.get_session(session_id="...")
   total_tokens = session.session_metrics.total_tokens
   ```

3. **Provider Data** (Gemini raw):
   ```python
   gemini_data = response.metrics.provider_metrics
   # Contains Gemini's native usage_metadata
   ```

### Best Practices

✅ **Always check** `response.metrics` exists before accessing  
✅ **Log token usage** for cost tracking and optimization  
✅ **Monitor session metrics** for user-level analytics  
✅ **Use cache** when possible to reduce costs  
✅ **Set token limits** to prevent runaway costs  

### Important Notes

- Token counts are **estimates** until the actual API call
- Agno's `metrics` includes **comprehensive data** beyond just tokens
- **Provider metrics** contains the raw Gemini response data
- **Session metrics** aggregate across all runs in a session
- Use **message-level metrics** for granular tracking

---

## Resources

- [Google Gemini Token Documentation](https://ai.google.dev/gemini-api/docs/tokens)
- [Agno Metrics Documentation](https://docs.agno.com/basics/sessions/metrics/overview)
- [Agno RunOutput Schema](https://docs.agno.com/reference/agents/run-response)
