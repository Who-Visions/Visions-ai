# 💰 Visions AI Cost Analysis

> **Last Updated**: 2025-12-07
> **Source**: Google Cloud Pricing Export (Contract Rates)

---

## 📊 Model Pricing Summary

### Vertex AI Models (Production)

| Model | Input (per 1M tokens) | Output (per 1M tokens) | Notes |
|-------|----------------------|------------------------|-------|
| **Gemini 3.0 Pro** | $2.00 | $12.00 | Global endpoint only |
| **Gemini 3.0 Pro Image** | $2.00 (image) | **$120.00** | Native image generation |
| **Gemini 2.5 Pro** | $1.25 | $10.00 | Deep thinking |
| **Gemini 2.5 Pro Thinking** | $1.25 | $10.00 | Extended reasoning |
| **Gemini 2.5 Flash** | $0.30 | $2.50 | Grounded search |
| **Gemini 2.5 Flash Thinking** | $0.30 | $2.50 | With thinking tokens |
| **Gemini 2.5 Flash Lite** | $0.10 | $0.40 | Triage/Quick instinct |
| **Gemini 2.5 Flash Image** | $0.30 | $30.00 | Fallback image gen |

### Multimodal Inputs

| Model | Video Input | Audio Input | Image Input |
|-------|-------------|-------------|-------------|
| **Gemini 2.5 Flash** | $0.30/1M | $1.00/1M | N/A |
| **Gemini 3.0 Pro** | N/A | N/A | $2.00/1M |

### Image & Video Generation

| Model | Cost per Generation |
|-------|---------------------|
| **Imagen 3** | $0.04/image |
| **Veo 3 Audio Video** | $0.40/video |

### Additional Services

| Service | Cost | Notes |
|---------|------|-------|
| **Google Search Grounding** | $35.00/1K requests | First 1,500 free/month |
| **Text Embeddings** | $0.000025/1K chars | Very cheap |

---

## 🧠 Visions AI Cascade Cost Breakdown

### Per-Query Cost Estimate (Typical Query)

Assuming average tokens per query:
- **Input**: ~500 tokens
- **Output**: ~1,000 tokens per model

```
┌─────────────────────────────────────────────────────────────────┐
│                     VISIONS CASCADE COST                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1️⃣ TRIAGE (Flash-Lite)                                         │
│     Input:  500 tokens × $0.10/1M = $0.00005                    │
│     Output: 200 tokens × $0.40/1M = $0.00008                    │
│     Subtotal: ~$0.00013                                         │
│                                                                  │
│  2️⃣ GROUNDED SEARCH (Flash + Google Search)                     │
│     Input:  500 tokens × $0.30/1M = $0.00015                    │
│     Output: 500 tokens × $2.50/1M = $0.00125                    │
│     Search: 1 request × $0.035    = $0.035 (after free tier)    │
│     Subtotal: ~$0.0364                                          │
│                                                                  │
│  3️⃣ DEEP THINKING (2.5 Pro)                                     │
│     Input:  1000 tokens × $1.25/1M = $0.00125                   │
│     Output: 1000 tokens × $10.00/1M = $0.01                     │
│     Subtotal: ~$0.01125                                         │
│                                                                  │
│  4️⃣ SYNTHESIS (Gemini 3 Pro)                                    │
│     Input:  3000 tokens × $2.00/1M = $0.006                     │
│     Output: 1500 tokens × $12.00/1M = $0.018                    │
│     Subtotal: ~$0.024                                           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│  💵 TOTAL PER QUERY (Full Cascade): ~$0.072                      │
│                                                                  │
│  📊 Cost by Route:                                               │
│     • Simple greeting (Skip cascade):    ~$0.0001               │
│     • Quick question (Flash only):       ~$0.002                │
│     • Grounded search query:             ~$0.04                 │
│     • Complex analysis (Full cascade):   ~$0.07                 │
│     • Image generation (+G3 Pro Image):  ~$0.15+                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 Image Generation Costs

### Gemini 3 Pro Image Preview (Flagship)

**Most Expensive** - Use wisely!

| Operation | Cost |
|-----------|------|
| Text prompt input | $2.00/1M tokens |
| **Image output** | **$120.00/1M tokens** |

Typical image generation (~1K output tokens):
- **Cost per image: ~$0.12**

### Gemini 2.5 Flash Image (Fallback)

| Operation | Cost |
|-----------|------|
| Text prompt input | $0.30/1M tokens |
| Image output | $30.00/1M tokens |

Typical image generation:
- **Cost per image: ~$0.03**

### Imagen 3 (Alternative)

- **Fixed cost: $0.04/image**

---

## 🖥️ Infrastructure Costs

### Reasoning Engine (Agent Hosting)

| Resource | Free Tier | Paid Rate |
|----------|-----------|-----------|
| CPU | 50 hours/month | $0.0994/hour |
| Memory | 93 GiB-hours/month | $0.0105/GiB-hour |

Estimated monthly cost (assuming 24/7 operation):
- CPU: 720 hours × $0.0994 = **$71.57/month**
- Memory (2 GiB): 1,440 GiB-hours × $0.0105 = **$15.12/month**
- **Total: ~$87/month** (after free tier)

### Cloud Storage

| Usage | Free Tier | Cost |
|-------|-----------|------|
| Storage | 5 GiB | $0.02/GiB-month |
| Class A Ops | 5K | $0.005/1K |
| Class B Ops | 50K | $0.0004/1K |
| Egress | 100 GiB | $0.12/GiB |

---

## 📈 Monthly Cost Projections

### Light Usage (100 queries/day)

```
Queries:     3,000/month
Avg Cost:    $0.03/query (mixed complexity)
─────────────────────────────
Query Costs: $90/month
Infra:       $87/month (Reasoning Engine)
Storage:     $5/month
─────────────────────────────
TOTAL:       ~$182/month
```

### Medium Usage (500 queries/day)

```
Queries:     15,000/month
Avg Cost:    $0.04/query
─────────────────────────────
Query Costs: $600/month
Infra:       $87/month
Storage:     $10/month
Grounding:   $470/month (13.5K requests @ $35/1K)
─────────────────────────────
TOTAL:       ~$1,167/month
```

### Heavy Usage (2,000 queries/day)

```
Queries:     60,000/month
Avg Cost:    $0.05/query
─────────────────────────────
Query Costs: $3,000/month
Infra:       $87/month
Storage:     $20/month
Grounding:   $2,047/month (58.5K requests @ $35/1K)
─────────────────────────────
TOTAL:       ~$5,154/month
```

---

## 💡 Cost Optimization Strategies

### 1. Smart Routing (Already Implemented ✅)

```python
# Skip expensive models for simple queries
if intent == "greeting":
    # Use only Flash-Lite: $0.0001 vs $0.07
    return quick_response()
```

**Savings: 99.9% on simple queries**

### 2. Grounding Cache

Implement 1-hour cache for search grounding results:
```python
# Same search within 1 hour = 0 cost
@cache(ttl=3600)
def grounded_search(query):
    ...
```

**Savings: 50-80% on grounding costs**

### 3. Use Flash Lite for Triage

Always route through Flash Lite first:
- $0.10/1M input vs $2.00/1M for G3 Pro
- **20x cheaper** for query analysis

### 4. Image Generation Fallback

```python
# Use Gemini 2.5 Flash Image for drafts
# Use Gemini 3 Pro Image for finals only
def generate_image(prompt, quality="draft"):
    if quality == "draft":
        return flash_image(prompt)  # $0.03
    else:
        return g3_pro_image(prompt)  # $0.12
```

**Savings: 75% on draft images**

### 5. Context Window Management

Keep conversation context under 128K tokens:
- G3 Pro: Long context = higher costs
- Trim old messages regularly

---

## 🎯 Cost Per Feature

| Feature | Avg Cost | Notes |
|---------|----------|-------|
| Text conversation | $0.02-0.07 | Depends on complexity |
| Camera recommendation | $0.04 | Grounded search |
| Image analysis | $0.03 | Flash + G3 Pro |
| Image generation (G3) | $0.12 | Flagship quality |
| Image generation (Flash) | $0.03 | Good quality |
| YouTube video analysis | $0.05 | Flash video input |
| PDF analysis | $0.02 | Flash document |

---

## 📊 Cost Tracking Implementation

Add to `agent.py`:

```python
class CostTracker:
    PRICES = {
        "gemini-3-pro-preview": {"input": 2.00, "output": 12.00},
        "gemini-3-pro-image-preview": {"input": 2.00, "output": 120.00},
        "gemini-2.5-pro": {"input": 1.25, "output": 10.00},
        "gemini-2.5-flash": {"input": 0.30, "output": 2.50},
        "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
        "grounding": 0.035,  # per request
    }
    
    def calculate_cost(self, model, input_tokens, output_tokens):
        prices = self.PRICES.get(model, {"input": 0, "output": 0})
        return (input_tokens * prices["input"] + 
                output_tokens * prices["output"]) / 1_000_000
```

---

## 🔥 Key Takeaways

1. **Gemini 3 Pro Image Output is EXPENSIVE**: $120/1M tokens
   - Use sparingly, prefer Flash Image for drafts

2. **Google Search Grounding adds up**: $35/1K after free tier
   - Cache results aggressively

3. **Flash Lite is your friend**: 20x cheaper than G3 Pro
   - Use for all triage/routing decisions

4. **Reasoning Engine is a fixed cost**: ~$87/month
   - Amortize across all queries

5. **Smart routing = massive savings**: 
   - Skip heavy models for simple queries
   - Route 1,000 greetings for $0.10 vs $70

---

*Generated by Gemini - Web & Cloud Specialist*
