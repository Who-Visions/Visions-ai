# Gemini Function Calling Reference

*Dec 2025 Specifications*

## Core Concepts

- **Purpose**: Connect models to external tools (APIs, databases).
- **Process**: Model returns `functionCall` -> App executes -> App sends `functionResponse`.
- **Modes**:
  - `AUTO`: Default. Model decides.
  - `ANY`: Forced function call.
  - `NONE`: Disable function calling.

## Gemini 3 Specifics (CRITICAL)

- **Thought Signatures**: mandatory for function calling.
  - **Single FC**: Signature on the function call part.
  - **Parallel FC**: Signature on the *first* function call part only.
  - **Requirement**: You must pass back the signature in the exact part it was received in the next turn.

## Advanced Features

- **Parallel Function Calling**: Execute multiple independent functions at once.
- **Compositional Function Calling**: Chain functions (e.g., Get Location -> Get Weather).
- **Multimodal Responses**: Return Images/PDFs in `functionResponse` (Gemini 3 only).

## Usage Example (Python)

```python
tools = types.Tool(function_declarations=[my_function])
tool_config = types.ToolConfig(
    function_calling_config=types.FunctionCallingConfig(mode='AUTO')
)
```
