# 🦝 Bandit Integration Guide: Visions Fleet Compliance

To bring **Bandit** online and responsive within the Visions Fleet, ensure the deployment meets the following standards.

## 1. Model Standard: Gemini 3

Bandit MUST use Gemini 3 Preview models. Avoid legacy 1.5/2.0 models.

* **Flash**: `gemini-3-flash-preview` (Speed/Tools)
* **Pro**: `gemini-3-pro-preview` (Reasoning/Vision)

## 2. API Endpoints

The `Visions-ai` connector expects specific endpoints. If paths differ, the connector will attempt fallbacks.

| Endpoint | Method | Required Response |
| :--- | :--- | :--- |
| `/health` | `GET` | `{"status": "online", "agent": "Bandit"}` |
| `/chat` | `POST` | Accepts `{"message": "..."}`, returns `{"response": "..."}` |
| `/.well-known/agent.json` | `GET` | Serves the **Agent Card** for fleet discovery. |

> [!TIP]
> If using OpenAI-compatible routing (e.g., `/v1/chat/completions`), ensure the top-level request field is `message` or `prompt` for easiest integration with the current fleet script.

## 3. IAM Permissions

Ensure the Bandit Cloud Run service account has the following role in project `metal-cable-478318-g8`:

* **Vertex AI User** (`roles/aiplatform.user`)

## 4. Docker & Entrypoint

Common failure point: `ModuleNotFoundError`.

* Ensure the `CMD` in `Dockerfile` matches the internal folder structure.
* Example: `CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]`

## 5. Fleet Test

Once deployed, verify integration from the `Visions-ai` console:

```powershell
python test_fleet_connectivity.py --agent bandit
```
