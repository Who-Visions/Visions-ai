# Gemini Model Specifications (As of Dec 26, 2025)

## 💎 Gemini 3 Series (The Standard)

**Strict Rule**: Use these models for ALL tasks unless a specific capability is explicitly "Not supported".

### Gemini 3 Pro (`gemini-3.1-pro-preview`)

* **Role**: Primary Agentic Brain, Deep Reasoning, Coding.
* **Context**: 1M Input / 65k Output.
* **Capabilities**:
  * ✅ Thinking (Reasoning)
  * ✅ Batch API
  * ✅ Caching & File Search
  * ✅ Code Execution & Function Calling
  * ✅ Search Grounding & URL Context
  * ✅ Structured Outputs
* **unsupported**: Audio Gen, Image Gen, Live API, Maps Grounding.

### Gemini 3 Flash (`gemini-3-flash-preview`)

* **Role**: High-Speed Triage, Real-time Search, Lightweight Ops.
* **Context**: 1M Input / 65k Output.
* **Capabilities**: Same as Pro, but faster/cheaper.
* **unsupported**: Audio Gen, Image Gen, Live API, Maps Grounding.

### Gemini 3 Pro Image (`gemini-3-pro-image`)

* **Role**: High-Fidelity Image Generation & Editing.
* **Context**: 65k Input / 32k Output.
* **Capabilities**:
  * ✅ Image Generation
  * ✅ Thinking (!)
  * ✅ Search Grounding
* **unsupported**: Code Exec, Function Calling, Caching.

---

## 🛠️ Gemini 2.5 Series (Legacy / Capability Fallbacks)

**Strict Rule**: ONLY use these for tools that Gemini 3 cannot do.

### Gemini 2.5 Flash Live (`gemini-3.1-flash-live-preview`)

* **Use Case**: **Voice Mode / Live API**.
* **Reason**: Gemini 3 does not support Live API yet.

### Gemini 2.5 Flash TTS (`gemini-3.1-flash-live-preview`)

* **Use Case**: **Text-to-Speech**.
* **Reason**: Gemini 3 does not support Audio Generation.

### Gemini 2.5 Flash (`gemini-3.6-flash`)

* **Use Case**: **Google Maps Operations**.
* **Reason**: Gemini 3 does not support Maps Grounding.
