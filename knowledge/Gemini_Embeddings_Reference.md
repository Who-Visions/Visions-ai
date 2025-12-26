# Gemini Embeddings Reference

*Dec 2025 Specifications*

**Model Code:** `gemini-embedding-001`
**Latest Update:** June 2025
**Input Token Limit:** 2,048
**Output Dimensions:** 128 - 3072 (Flexible)

## Overview

Gemini Embeddings (`gemini-embedding-001`) power semantic search, classification, clustering, and RAG. They support **Matryoshka Representation Learning (MRL)**, allowing for flexible output dimensionality without retraining.

## Key Features

### 1. Dimensionality Control

Reduce storage/compute by truncating embeddings.

- **Default:** 3072 dimensions
- **Recommended:** 768, 1536, or 3072
- **Performance:** Lower dimensions (e.g., 768) retain ~99% of performance (MTEB 67.99 vs 68.16).

**Code Example (Python):**

```python
config = types.EmbedContentConfig(output_dimensionality=768)
```

*Note: Dimensions other than 3072 must be normalized (L2 norm) before use.*

### 2. Task Types

Optimize embeddings for specific use cases.

| Task Type | Description |
| :--- | :--- |
| `SEMANTIC_SIMILARITY` | (Default) Assessing text similarity (STS, Duplicate detection). |
| `RETRIEVAL_DOCUMENT` | Documents to be indexed/retrieved. |
| `RETRIEVAL_QUERY` | Queries used to find documents. |
| `CLASSIFICATION` | Sentiment analysis, labeling. |
| `CLUSTERING` | Grouping similar items. |
| `QUESTION_ANSWERING` | Questions in a QA system. |
| `FACT_VERIFICATION` | Statements to be verified. |

**Code Example (Python):**

```python
config = types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
```

### 3. Batch API

High throughput, 50% cost reduction.

- Use `batchEmbedContents` (REST) or list inputs (SDK).

## Implementation Guides

### Python SDK (`google-genai`)

```python
from google import genai
from google.genai import types

client = genai.Client()

result = client.models.embed_content(
    model="gemini-embedding-001",
    contents=["Meaning of life?", "How to bake cake?"],
    config=types.EmbedContentConfig(
        task_type="SEMANTIC_SIMILARITY",
        output_dimensionality=768
    )
)

for embedding in result.embeddings:
    print(embedding.values[:5]) # First 5 values
```

### Normalization (Required for < 3072 dims)

```python
import numpy as np

values = np.array(embedding_obj.values)
normed = values / np.linalg.norm(values)
```

## Best Practices

- **RAG:** Use `RETRIEVAL_QUERY` for user questions and `RETRIEVAL_DOCUMENT` for your knowledge base chunks.
- **Efficiency:** Use 768 dimensions for a good balance of quality and speed/cost.
- **Batching:** Always batch inputs when processing multiple texts.
