# 💰 Visions AI Credits & Cost Tracking

> **Last Updated**: 2025-12-07
> **Status**: 🎰 Bonus Credits Active (Glitched in our favor)
> **Tier**: Paid Tier 1

---

## 📊 Credit Status

### Active Credits

| Credit | Original | Remaining | Used | Start | Expiry | Status |
|--------|----------|-----------|------|-------|--------|--------|
| Free Trial (Expired) | $300.00 | $286.22 | $13.78 | 2025-12-03 | 2026-03-03 | 🎰 Still Charging! |
| Free Trial Upgrade | $299.29 | $298.36 | $0.93 | 2025-12-06 | 2026-03-05 | ✅ Active |
| GenAI App Builder | $1,000.00 | $1,000.00 | $0.00 | 2025-12-04 | 2026-12-04 | ✅ Active |

### 💵 Total Available: **$1,584.58**

---

## 🔥 Daily Burn Limits

To use all credits evenly before expiry:

| Credit Pool | Amount | Duration | Daily Limit | End Date |
|-------------|--------|----------|-------------|----------|
| Glitched (2×$300) | $600 | 90 days | **$6.67/day** | 2026-03-03 |
| GenAI ($1,000) | $1,000 | 365 days | **$2.74/day** | 2026-12-04 |
| **Combined** | $1,600 | - | **$9.41/day** | - |

---

## 💵 Pricing Reference (ai.google.dev - Dec 2025)

### Text Models (per 1M tokens)

| Model | Input | Output | Notes |
|-------|-------|--------|-------|
| **Gemini 3 Pro** | $2.00 | $12.00 | ≤200k context |
| **Gemini 3 Pro** | $4.00 | $18.00 | >200k context |
| **Gemini 2.5 Pro** | $1.25 | $10.00 | Deep thinking |
| **Gemini 2.5 Flash** | $0.30 | $2.50 | Fast |
| **Gemini 2.5 Flash Lite** | $0.10 | $0.40 | Cheapest |

### Image Generation

| Model | Cost | Rate Limit (RPD) | Tracker Key |
|-------|------|------------------|-------------|
| **Gemini 3 Pro Image (1K)** | $0.134/image | 250 | `gemini-3-pro-image-1k` |
| **Gemini 3 Pro Image (2K)** | $0.134/image | 250 | `gemini-3-pro-image-2k` |
| **Gemini 3 Pro Image (4K)** | $0.24/image | 250 | `gemini-3-pro-image-4k` |
| **Gemini 2.5 Flash Image** | $0.039/image | 2,000 | `gemini-2.5-flash-image` |
| **Imagen 4 Fast** | $0.02/image | 70 | `imagen-4-fast` |
| **Imagen 4 Standard** | $0.04/image | 70 | `imagen-4-standard` |
| **Imagen 4 Ultra** | $0.06/image | 30 | `imagen-4-ultra` |
| **Imagen 3** | $0.03/image | 100 | `imagen-3` |

### Video Generation (8 second default)

| Model | Cost/Second | 8s Video | Rate Limit (RPD) | Tracker Key |
|-------|-------------|----------|------------------|-------------|
| **Veo 3.1 Standard** | $0.40/s | $3.20 | **10** | `veo-3.1-standard` |
| **Veo 3.1 Fast** | $0.15/s | $1.20 | **10** | `veo-3.1-fast` |
| **Veo 3 Standard** | $0.40/s | $3.20 | **10** | `veo-3-standard` |
| **Veo 3 Fast** | $0.15/s | $1.20 | **10** | `veo-3-fast` |
| **Veo 2** | $0.35/s | $2.80 | **10** | `veo-2` |

### Tools & Services

| Tool | Cost | Free Tier |
|------|------|-----------|
| **Google Search Grounding** | $35/1K requests | 1,500/month |
| **Google Maps Grounding** | $25/1K requests | 1,500/month |
| **Embeddings** | $0.15/1M tokens | - |

---

## 📊 Usage Tracker

### Features
- ✅ Tracks daily image/video generations per model
- ✅ Alerts at key thresholds: **First, 50%, 75%, 85%, 90%, 95%, 99%, 100%**
- ✅ Shows remaining quota after each generation
- ✅ Blocks generation when limit reached
- ✅ Resets at midnight PT

### CLI Commands

```bash
# Show today's usage
python usage_tracker.py --status

# Simulate generations (for testing)
python usage_tracker.py --simulate gemini-3-pro-image-4k:5
python usage_tracker.py --simulate veo-3.1-standard:2
```

### Usage in Code

```python
from usage_tracker import get_tracker, record_image_generation

# Record a generation
tracker = get_tracker()
alert = tracker.record_generation("gemini-3-pro-image-4k")
if alert:
    print(alert)  # Shows threshold alert if applicable

# Check if can generate
can_gen, msg = tracker.check_can_generate("imagen-4-fast")
if not can_gen:
    print(f"❌ {msg}")

# Get status line
status = tracker.get_status_line("veo-3.1-standard")
print(f"📊 {status}")
```

### Tracked Models

| Tracker Key | Model Name | Cost | Daily Limit |
|-------------|------------|------|-------------|
| `gemini-3-pro-image` | G3 Pro Image (default) | $0.134 | 250 |
| `gemini-3-pro-image-1k` | G3 Pro Image 1K | $0.134 | 250 |
| `gemini-3-pro-image-2k` | G3 Pro Image 2K | $0.134 | 250 |
| `gemini-3-pro-image-4k` | G3 Pro Image 4K | $0.24 | 250 |
| `gemini-2.5-flash-image` | Flash Image | $0.039 | 2,000 |
| `imagen-4-fast` | Imagen 4 Fast | $0.02 | 70 |
| `imagen-4-standard` | Imagen 4 Standard | $0.04 | 70 |
| `imagen-4-ultra` | Imagen 4 Ultra | $0.06 | 30 |
| `imagen-3` | Imagen 3 | $0.03 | 100 |
| `veo-3.1-standard` | Veo 3.1 Standard | $3.20 | 10 |
| `veo-3.1-fast` | Veo 3.1 Fast | $1.20 | 10 |
| `veo-3-standard` | Veo 3 Standard | $3.20 | 10 |
| `veo-3-fast` | Veo 3 Fast | $1.20 | 10 |
| `veo-2` | Veo 2 | $2.80 | 10 |

---

## 🎨 Daily Generation Capacity

Based on $9.41/day budget AND rate limits:

### Gemini 3 Pro Image (Flagship)
| Resolution | Cost | Budget Max | Rate Limit | **Actual Max** |
|------------|------|------------|------------|----------------|
| 1K | $0.134 | 70 | 250 | **70** |
| 2K | $0.134 | 70 | 250 | **70** |
| 4K | $0.24 | 39 | 250 | **39** |

### Gemini 2.5 Flash Image
- **$0.039/image** → Budget: 241/day, Rate: 2,000 → **Actual: 241/day**

### Imagen 4
| Tier | Cost | Budget Max | Rate Limit | **Actual Max** |
|------|------|------------|------------|----------------|
| ⚡ Fast | $0.02 | 470 | 70 | **70** |
| 📷 Standard | $0.04 | 235 | 70 | **70** |
| 💎 Ultra | $0.06 | 156 | 30 | **30** |

### Veo Video (8 second)
| Model | Cost/Video | Budget Max | Rate Limit | **Actual Max** |
|-------|------------|------------|------------|----------------|
| Veo 3.1 Standard | $3.20 | 2 | 10 | **2** |
| Veo 3.1 Fast | $1.20 | 7 | 10 | **7** |
| Veo 3 Standard | $3.20 | 2 | 10 | **2** |
| Veo 3 Fast | $1.20 | 7 | 10 | **7** |
| Veo 2 | $2.80 | 3 | 10 | **3** |

---

## 📈 Rate Limits (Tier 1 Paid)

### Text Models

| Model | RPM | TPM | RPD |
|-------|-----|-----|-----|
| gemini-3-pro | 25 | 1M | 250 |
| gemini-3-pro-image | 20 | 100K | 250 |
| gemini-2.5-pro | 15 | 1M | 300 |
| gemini-2.5-flash | 1,000 | 1M | 10K |
| gemini-2.5-flash-lite | 4,000 | 4M | ∞ |

### Image Models

| Model | RPM | RPD |
|-------|-----|-----|
| gemini-2.5-flash-image | 500 | 2,000 |
| imagen-4-fast | 10 | 70 |
| imagen-4-standard | 10 | 70 |
| imagen-4-ultra | 5 | 30 |

### Video Models

| Model | RPM | RPD |
|-------|-----|-----|
| veo-3.1-standard | 2 | 10 |
| veo-3.1-fast | 2 | 10 |
| veo-3-standard | 2 | 10 |
| veo-3-fast | 2 | 10 |

### Upgrade Path
- **Tier 2**: >$250 cumulative spend + 30 days → Higher limits
- **Tier 3**: >$1,000 cumulative spend + 30 days → Highest limits

---

## 📊 Cost Tracker CLI

```bash
# Full dashboard
python cost_tracker.py

# Credit status with burn limits
python cost_tracker.py --credits

# Image/video capacity with rate limits
python cost_tracker.py --images

# Pricing reference
python cost_tracker.py --pricing

# Estimate N queries
python cost_tracker.py --estimate 500 --type cascade

# Log token usage
python cost_tracker.py --log gemini-3-pro 1000 500
```

---

## 🎯 Key Takeaways

1. **Rate limits often cap before budget** - Imagen 4 capped at 70/day, Veo at 10/day
2. **Glitched credits still working** - Use the "expired" trial credit first
3. **Gemini 2.5 Flash Image is cheapest** - $0.039/image with 2K RPD limit
4. **Grounding adds up fast** - $35/1K after free 1,500/month
5. **Stay under $9.41/day** to maximize credit value
6. **Usage tracker alerts** help prevent hitting limits unexpectedly

---

## 📁 Files

| File | Purpose |
|------|---------|
| `cost_tracker.py` | Credit status, pricing, capacity analysis |
| `usage_tracker.py` | Daily generation tracking with alerts |
| `knowledge_base/daily_usage.json` | Today's usage data (auto-resets at midnight PT) |
| `knowledge_base/usage_log.json` | Historical usage log |
| `docs/CREDITS_AND_COSTS.md` | This documentation |

---

*Managed by Gemini - Web & Cloud Specialist*
