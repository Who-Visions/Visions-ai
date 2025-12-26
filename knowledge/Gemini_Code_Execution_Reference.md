# Gemini Code Execution Reference

*Dec 2025 Specifications*

## Overview

Built-in Python sandbox for math, data processing, and "Visual Thinking".

## Visual Thinking (Gemini 3 Flash)

- **Capability**: Can "Zoom and Inspect" images or perform "Visual Math".
- **Activation**: Enable `code_execution` + `thinking`.
- **Flow**: Model writes code to crop/analyze image -> executes -> refines answer.

## Input / Output

- **Inputs**: Text, CSV, PDF, Images (via `part.inlineData` or `fileData`).
- **Outputs**: Text, Matplotlib Graphs (returned as inline images).
- **Billing**: Generated code + Output = "Output Tokens".

## Implementation

```python
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[image, "Count the gears"],
    config=types.GenerateContentConfig(
        tools=[types.Tool(code_execution=types.ToolCodeExecution)]
    )
)
```

## Supported Libraries

`numpy`, `pandas`, `matplotlib`, `scipy`, `sklearn`, `openpyxl`, `sympy`, etc.
*No internet access in sandbox (except specific allowlists).*
