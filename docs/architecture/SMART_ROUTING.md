# Visions AI - Smart Routing Architecture

**Version**: 2.2.0
**Implemented**: 2026-02-06
**Status**: 🟢 Active
**Component**: `VisionsAgent.query`

---

## 🌐 The 6-Level Heuristic Ladder

Visions AI uses a "Pulse-Check" system to route every query. It first pings **Gemini 3 Flash** for an initial complexity assessment (1-10) and then routes the query to one of 6 reasoning tiers.

### Triage Phase (Pulse Check)
*   **Model**: `gemini-3-flash-preview`
*   **Task**: "Categorize query. Respond JSON: {'is_high_risk': bool, 'complexity': 1-10, 'needs_search': bool}"
*   **Latency**: ~0.3s

### Routing Tiers

| Tier | Complexity | Risk | Model | Thinking Level | Use Case |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | 1 | Low | **Flash** | `MINIMAL` | Greetings, basic facts, latency-critical ops. |
| **2** | 2-3 | Low | **Flash** | `LOW` | Standard Q&A, simple summaries. |
| **3** | 4-5 | Low | **Flash** | `MEDIUM` | Balanced reasoning, creative writing drafts. |
| **4** | 6 | Low | **Flash** | `HIGH` | Complex logic needing speed (code snippets). |
| **5** | 7-8 | Low | **Pro** | `LOW` | High-quality creative work, strategic advice. |
| **6** | 9-10 | Any | **Pro** | `HIGH` | Critical analysis, deep research, high-risk topics. |

### Technical Implementation

The router resides in `visions/core/agent.py`:

```python
if is_high_risk or complexity >= 9:
    target_model = Config.MODEL_PRO
    thinking_level = Config.THINKING_LEVEL_HIGH
elif complexity >= 7:
    target_model = Config.MODEL_PRO
    thinking_level = Config.THINKING_LEVEL_LOW
elif complexity >= 6:
    target_model = Config.MODEL_FLASH
    thinking_level = Config.THINKING_LEVEL_HIGH
# ... lower tiers
```

### Why this architecture?
1.  **Cost Efficiency**: 90% of queries stay on Flash (Tiers 1-4).
2.  **Latency Optimization**: Tier 1-2 responses are near-instant.
3.  **Maximum Intelligence**: When needed (Tier 6), the full reasoning power of Gemini 3 Pro is unleashed.
