# Gemini 3 Flash Preview - Official Pricing (Jan 2026)

## Your Model Configuration

**Model**: `gemini-3-flash-preview`

This is the most intelligent model built for speed, combining frontier intelligence with superior search and grounding.

---

## Standard Pricing (Per 1M Tokens)

### Free Tier
- ✅ Input price: **Free of charge**
- ✅ Output price: **Free of charge**
- ✅ Context caching: **Free of charge**
- ⚠️ Content used to improve Google's products

### Paid Tier
| Component | Price per 1M tokens |
|-----------|-------------------|
| **Input tokens** | **$0.50** (text, image, video) |
| **Output tokens** | **$3.00** (including thinking tokens) |
| **Context caching** | **$0.05** (text, image, video) |
| **Storage** | **$1.00 per 1M tokens/hour** |

---

## Batch Pricing (50% Cost Reduction)

### Free Tier
- Not available for batch

### Paid Tier
| Component | Price per 1M tokens |
|-----------|-------------------|
| **Input tokens** | **$0.25** (text, image, video) |
| **Output tokens** | **$1.50** (including thinking tokens) |
| **Context caching** | **$0.05** (text, image, video) - same as Standard |
| **Storage** | **$1.00 per 1M tokens/hour** - same as Standard |

---

## Cost Calculation Examples

### Standard API Pricing

**Example 1: Simple Query**
- Input: 50 tokens
- Output: 200 tokens
- Cost: (50 × $0.50 + 200 × $3.00) / 1,000,000 = **$0.00061** (~0.06¢)

**Example 2: Medical Query with Knowledge Base Search**
- Input: 500 tokens (including knowledge base context)
- Output: 1,000 tokens (comprehensive medical response)
- Cost: (500 × $0.50 + 1,000 × $3.00) / 1,000,000 = **$0.00350** (~0.35¢)

**Example 3: Complex Multi-book Comparison**
- Input: 2,000 tokens (multiple knowledge base searches)
- Output: 2,500 tokens (detailed comparison)
- Cost: (2,000 × $0.50 + 2,500 × $3.00) / 1,000,000 = **$0.00850** (~0.85¢)

---

## Batch API Pricing (50% Savings)

**Example: Processing 100 Medical Queries**
- Per-query input: 500 tokens
- Per-query output: 1,000 tokens
- Cost per query: (500 × $0.25 + 1,000 × $1.50) / 1,000,000 = **$0.00175** (~0.175¢)
- Total for 100 queries: **$0.175** (~1.75¢)

---

## Audio Pricing

| Component | Price per 1M tokens |
|-----------|-------------------|
| Audio input | **$1.00** |
| Audio caching | **$0.10** |

---

## Grounding with Google Search

| Type | Free Limit | After Free |
|------|-----------|-----------|
| Standard API | 5,000 prompts/month | $14 per 1,000 queries |
| Batch API | 1,500 RPD (requests per day) | $14 per 1,000 queries |

**Status**: Coming soon (starting January 5, 2026)

---

## Comparison: Previous vs Current Pricing

### Previous (Gemini 2.0 Flash)
- Input: $0.075 per 1M tokens
- Output: $0.30 per 1M tokens

### Current (Gemini 3 Flash Preview)
- Input: **$0.50 per 1M tokens** (6.67x more expensive)
- Output: **$3.00 per 1M tokens** (10x more expensive)

**Impact**: Your Medical Bot is now 8-10x more expensive per token, but with significantly better intelligence.

---

## Cost Optimization Strategies

### 1. Use Context Caching
Save **90%** on cached prompts:
- Fresh input: $0.50 per 1M tokens
- Cached input: $0.05 per 1M tokens
- **Ideal for**: Repeated knowledge base searches, system prompts, medical guidelines

### 2. Use Batch API
Save **50%** on non-urgent requests:
- Standard: $0.50 input + $3.00 output per 1M
- Batch: $0.25 input + $1.50 output per 1M
- **Ideal for**: Bulk medical report processing, research analysis

### 3. Optimize Input Tokens
- Compress prompts
- Use fewer examples in few-shot learning
- Implement smart knowledge base filtering
- Cache system prompts and guidelines

### 4. Reduce Output Tokens
- Set `max_output_tokens` appropriately
- Use structured outputs to reduce verbose responses
- Implement token budgets for different query types

---

## Monitoring Your Usage

To track costs in your Medical Bot, use the metrics provided:

```python
# From interactive_chat.py
input_cost = (metrics.input_tokens * 0.50) / 1_000_000
output_cost = (metrics.output_tokens * 3.00) / 1_000_000
total_cost = input_cost + output_cost
```

---

## Current Pricing in interactive_chat.py

⚠️ **ACTION REQUIRED**: Update pricing in your code!

Current (outdated - Gemini 2.0 Flash):
```python
input_cost = (metrics.input_tokens * 0.075) / 1_000_000
output_cost = (metrics.output_tokens * 0.30) / 1_000_000
```

Should be (Gemini 3 Flash Preview):
```python
input_cost = (metrics.input_tokens * 0.50) / 1_000_000
output_cost = (metrics.output_tokens * 3.00) / 1_000_000
```

---

## Sources

- Official Google Gemini Pricing: https://ai.google.dev/pricing
- Gemini API Documentation: https://ai.google.dev/gemini-api/docs
- Pricing Last Updated: January 2026

---

## Quick Reference

| Model | Input | Output | Best For |
|-------|-------|--------|----------|
| **Gemini 3 Flash** | $0.50/1M | $3.00/1M | ✅ Your model - Speed + Intelligence |
| Gemini 3 Pro | $2.00/1M | $12.00/1M | Multimodal + Agentic |
| Gemini 2.5 Pro | $1.25/1M | $10.00/1M | Coding + Complex reasoning |
| Gemini 2.5 Flash | Lower cost | Lower cost | Budget option |

