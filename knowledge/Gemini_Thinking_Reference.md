# Gemini Thinking & Thought Signatures Reference

*Dec 2025 Specifications*

## Thinking Levels (Gemini 3)

Controlled via `thinking_config.thinking_level`.

- **Gemini 3 Pro**: `low`, `high` (default).
- **Gemini 3 Flash**: `minimal`, `low`, `medium`, `high`.

## Thinking Budgets (Gemini 2.5)

Controlled via `thinking_config.thinking_budget`.

- **Dynamic**: `-1`
- **Disable**: `0`
- **Range**: `128` - `32768` tokens.

## Thought Signatures (CRITICAL)

Encrypted representations of internal reasoning.

- **Behavior**:
  - **Function Calls (Gemini 3)**: Signature attached to the *first* function call part.
  - **Non-Function Calls**: Signature attached to the *last* part (if thinking occurred).
- **Mandatory Requirement**: You **MUST** pass back the thought signature in the exact part it was received (e.g., the function call part) in the next turn.
  - **SDK**: AUtomatically handled if using `chat.send_message` or appending full response objects.
  - **Manual**: If manually constructing history, you must explicitly copy `thought_signature`.

### Validation Error

Missing signatures with Gemini 3 Function Calling results in `400 Bad Request`.

## Code Example (Manual Handling)

```python
# Helper to copy signature if present
if hasattr(part, 'thought_signature'):
    new_part.thought_signature = part.thought_signature
```
