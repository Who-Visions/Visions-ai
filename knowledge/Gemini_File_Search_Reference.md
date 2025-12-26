# Gemini File Search Reference

*Dec 2025 Specifications*

## Overview

Managed RAG service. Upload files -> Auto-chunk & Embed -> Query via `file_search` tool.

## Key Features

- **Cost**: Storage & Retrieval = FREE. Indexing = $0.15/1M tokens.
- **Limits**: 100MB/file. 1GB Free Tier storage.
- **Models**: Gemini 3, 2.5 Pro/Flash.

## Implementation (Python)

1. **Create Store**: `store = client.file_search_stores.create(config={'display_name': 'MyStore'})`
2. **Upload**: `client.file_search_stores.upload_to_file_search_store(file='path/to/doc.pdf', file_search_store_name=store.name)`
3. **Query**:

```python
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="Summarize the doc",
    config=types.GenerateContentConfig(
        tools=[types.Tool(
            file_search=types.FileSearch(file_search_store_names=[store.name])
        )]
    )
)
```

## Metadata Filtering

Can filter by custom keys (e.g., `author="Google"`).
