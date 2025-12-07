# Vertex AI Quota Management Guide

## 🎯 Current Status
- **Project**: `endless-duality-480201-t3`
- **Model**: `gemini-3-pro-image-preview` (Global endpoint)
- **Latest Issue**: 429 RESOURCE_EXHAUSTED on image generation (Dec 5, 2025)
- **Solution**: Dual-mode system with AI Studio fallback ✅

---

## 📊 Quota Limits (Confirmed)

### Google AI Studio API (Fallback) ✅
**Confirmed limits for `gemini-3-pro-image-preview`:**

| Metric | Limit | Current Usage | Status |
|--------|-------|---------------|--------|
| **Requests per minute (RPM)** | 20 | 1 | ✅ 95% available |
| **Tokens per minute (TPM)** | 100,000 | 32 | ✅ 99.97% available |
| **Requests per day (RPD)** | 250 | 1 | ✅ 99.6% available |

**Dashboard**: [AI Studio Rate Limits](https://aistudio.google.com/app/apikey)

### Vertex AI (Primary)
Search for these quota names in the [GCP Quotas Console](https://console.cloud.google.com/iam-admin/quotas?project=endless-duality-480201-t3):

| Quota Name | Service | Recommended Alert Threshold |
|------------|---------|----------------------------|
| Generate content requests per minute (global) | Vertex AI API | 80% |
| Image generation requests per minute | Vertex AI API | 80% |
| Input tokens per minute | Vertex AI API | 75% |
| Output tokens per minute | Vertex AI API | 75% |

### Current Quotas in Use
| Quota | Current Usage | Limit | Status |
|-------|---------------|-------|--------|
| Reasoning Engine Entities (us-central1) | 18 | 100 | ✅ 18% |
| Query Reasoning Engine requests/min (us-central1) | 1 | 30 | ✅ 3.33% |
| Resource management (CRUD) requests/min | 1 | 600 | ✅ 0.17% |

---

## 🔍 How to Find Image Generation Quotas

1. **Navigate to**: [Quotas Console](https://console.cloud.google.com/iam-admin/quotas?project=endless-duality-480201-t3)
2. **In the Filter box**, search for:
   - `Generative AI`
   - `Gemini`
   - `Generate content`
   - `Image generation`
3. **Look for quotas with "Dimensions"**:
   - `location: global` (our current setup)
   - `model: gemini-3-pro-image-preview`

---

## 🚨 Setting Up Alerts

### Steps to Create Quota Alerts:
1. In the Quotas console, click on a quota row
2. Click the **"..." (more actions)** button
3. Select **"Set up quota alert"**
4. Configure:
   - **Threshold**: 80% (for critical quotas like image generation)
   - **Threshold**: 90% (for less critical quotas)
   - **Notification channel**: Add your email or Slack webhook

### Recommended Alert Configurations:

```yaml
Generate Content Requests (Global):
  threshold: 80%
  notification: email + slack
  priority: HIGH

Image Generation Requests:
  threshold: 75%
  notification: email + slack
  priority: CRITICAL

Token Quotas:
  threshold: 85%
  notification: email
  priority: MEDIUM
```

---

## ⚡ Quota Increase Requests

### If you need more quota for image generation:

1. **Navigate to the quota** in the console
2. Click **"Edit quotas"** or **"Request quota increase"**
3. **Justification template**:

```
Project: endless-duality-480201-t3
Service: Vertex AI Generative AI
Model: gemini-3-pro-image-preview
Location: global

Reason for request:
We are building a production photography AI assistant (Visions AI) that generates 
high-quality images for professional photography use cases. We anticipate:
- 100-200 image generation requests per hour during peak usage
- Need for consistent availability for user-facing application
- Using global endpoint to optimize availability

Current limit is insufficient for our production workload. Requesting increase to:
- Generate content requests: [X] per minute (specify desired limit)
- Image generation requests: [X] per minute (specify desired limit)
```

---

## 🛡️ Quota Exhaustion Mitigation Strategies

### 1. **Global Endpoint** (Already Implemented ✅)
```python
client = genai.Client(vertexai=True, project=PROJECT_ID, location='global')
```
- Reduces 429 errors by routing to available regions
- Already implemented in `agent.py` line 163

### 2. **Exponential Backoff with Retry**
Implement in `agent.py`:

```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

@retry(
    retry=retry_if_exception_type(Exception),  # Catch 429 errors
    wait=wait_exponential(multiplier=1, min=4, max=60),
    stop=stop_after_attempt(5)
)
def generate_with_retry(client, model, contents, config):
    return client.models.generate_content(
        model=model,
        contents=contents,
        config=config
    )
```

### 3. **Queue System for High-Volume Requests**
- Implement request queuing for image generation
- Rate limit to stay under quota (e.g., max 20 requests/min if quota is 30/min)
- Use Cloud Tasks or Pub/Sub for async processing

### 4. **Fallback Models**
Priority chain:
1. `gemini-3-pro-image-preview` (primary)
2. `gemini-2.5-flash-image` (fallback #1)
3. `imagen-3.0-generate-001` (fallback #2 via tools)

### 5. **Caching**
- Cache generated images by prompt hash
- Reuse previously generated images for similar prompts
- Store in GCS bucket: `gs://endless-duality-480201-t3-reasoning-artifacts/generated_images/`

---

## 📈 Monitoring Dashboard

### Key Metrics to Track:
- **Quota Usage %** (real-time from GCP console)
- **429 Error Rate** (from application logs)
- **Request Latency** (global endpoint routing time)
- **Fallback Usage** (how often we use alternative models)

### Log Analysis Query (Cloud Logging):
```
resource.type="vertex_ai_endpoint"
severity="ERROR"
jsonPayload.error.code=429
```

---

## 🔗 Useful Links

- [Vertex AI Quotas Console](https://console.cloud.google.com/iam-admin/quotas?project=endless-duality-480201-t3)
- [Vertex AI Quotas Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/quotas)
- [Error Code 429 Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429)
- [Global Endpoint Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/locations#global-endpoint)

---

## 📝 Next Steps

1. ✅ **Filter quotas** for "Generative AI" or "Gemini"
2. ⏳ **Identify** current image generation quota limits
3. ⏳ **Set up alerts** at 80% threshold
4. ⏳ **Request quota increase** if needed
5. ⏳ **Implement retry logic** with exponential backoff
6. ⏳ **Add fallback models** to agent.py

---

**Last Updated**: 2025-12-05  
**Maintainer**: Dave (Gemini Agent)
