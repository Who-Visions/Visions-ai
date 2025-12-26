# Gemini Structured Outputs Reference

*Dec 2025 Specifications*

## Capabilities

- **Native JSON**: Guarantees valid JSON output matching a provided schema.
- **Type Safety**: Supports `string`, `number`, `integer`, `boolean`, `object`, `array`, `enum`.
- **Tools + Structure**: Gemini 3 supports using Tools (Search, Code) *and* Structured Output simultaneously.

## Usage

Set `response_mime_type` to `application/json` and provide `response_json_schema`.

### Python (Pydantic)

```python
class Recipe(BaseModel):
    name: str
    ingredients: List[str]

config={
    "response_mime_type": "application/json",
    "response_json_schema": Recipe.model_json_schema(),
}
```

### Supported Models

- Gemini 3 Pro/Flash
- Gemini 2.5 Pro/Flash
- Gemini 2.0 Flash (requires propertyOrdering)

## Best Practices

- Use `description` fields heavily to guide the model.
- Use `enum` for classification.
- Prefer Structured Outputs for *final answers*, Function Calling for *intermediate actions*.
