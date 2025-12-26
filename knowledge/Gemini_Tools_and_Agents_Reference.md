# Gemini Tools & Agents Reference

*Dec 2025 Specifications*

## Built-in Tools

Managed by Google. Flow: Request -> Gemini executes -> Response.

1. **Google Search**: Grounding in real-time events.
2. **Google Maps**: Location-aware assistance.
3. **Code Execution**: Write and run Python for math/data.
4. **URL Context**: Read specific pages/docs.
5. **File Search**: RAG over indexed documents.
6. **Computer Use (Preview)**: Interact with browser UIs.

## Agents

1. **Deep Research**: Autonomously plans, executes, and synthesizes multi-step research.

## Frameworks

- LangChain / LangGraph
- LlamaIndex
- CrewAI
- Google ADK

## Structured Outputs with Tools (Gemini 3 Pro)

- Can combine **Structured Outputs** (schema enforcement) with **Built-in Tools**.
- *Example*: Use Google Search to find a recipe, but force the output into a `Recipe` JSON schema.
