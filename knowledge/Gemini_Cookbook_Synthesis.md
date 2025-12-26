# Gemini Cookbook Synthesis: Gold Standard Patterns

**Source**: `C:\Users\super\Watchtower\HQ_WhoArt\Colab` (Ingested Dec 26, 2025)

## 1. Code Execution (`code_execution.py`)

- **Configuration**:

  ```python
  tools=[types.Tool(code_execution=types.ToolCodeExecution)]
  ```

- **Capabilities**:
  - Can generate **outputs** (printed to stdout) and **plots** (saved/displayed).
  - Works with **uploaded files** (File API) referenced in potential prompts.
  - **Streaming**: Compatible with `generate_content_stream`. Chunks have `executable_code` or `execution_result`.
  - **Chat**: Works seamlessly with `chats.create`.
- **Multimodal**: Can process images + code requests (e.g., "Run simulation of Monty Hall based on this image").

## 2. Search Grounding (`search_grounding.py`)

- **Configuration**:

  ```python
  tools=[types.Tool(google_search=types.GoogleSearch())]
  ```

- **Metadata**:
  - `response.candidates[0].grounding_metadata`:
    - `web_search_queries`: List of queries used.
    - `grounding_chunks`: Source content.
    - `search_entry_point`: Rendered HTML for attribution (Critical for UI).
- **Tool Mixing**:
  - **Crucial**: Gemini 3 supports mixing `google_search` with custom tools (Function Calling).
  - Example: Search for weather -> Call `set_climate(mode, strength)`.

## 3. Function Calling (`function_calling.py`)

- **Parallel Calling**:
  - The model can call multiple *independent* functions in a single turn.
  - *No special config needed* for basic parallel calls (default behavior).
- **Compositional Calling**:
  - Model can chain calls across turns (Call A -> Result -> Call B).
- **Modes**:
  - `AUTO` (Default): Model decides.
  - `ANY`: Forces at least one tool call.
  - `NONE`: Forces text only.
- **Config**:

  ```python
  tool_config = types.ToolConfig(
      function_calling_config=types.FunctionCallingConfig(
          mode="auto", # or "any", "none"
          allowed_function_names=["func1"] # Optional restriction
      )
  )
  ```

## 4. File Search (`file_search.py`)

- **RAG-as-a-Tool**:
  - Managed stores via `client.file_search_stores`.
  - **Upload**: `client.file_search_stores.upload_to_file_search_store`.
  - **Usage**:

    ```python
    tools=[types.Tool(
        file_search=types.FileSearch(
            file_search_store_names=[store.name],
            top_k=5, # Control context size
            metadata_filter='string_key = "value"'
        )
    )]
    ```

- **Citations**:
  - `grounding_metadata.grounding_supports` links generated text spans to source chunks.
  - **Best Practice**: Use `grounding_supports` to render superscript citations in UI.

## 5. Thinking (`get_started_thinking.py`)

- **Gemini 2.5 Policy**: Use `thinking_budget` (int).
- **Gemini 3 Policy**: Use `thinking_level` (`minimal` | `low` | `medium` | `high`).
  - **Thinking Config**:

    ```python
    thinking_config=types.ThinkingConfig(
        include_thoughts=True,
        thinking_level="HIGH"
    )
    ```

- **Thought Retrieval**:
  - Thoughts come in `candidates[0].content.parts` as text-like parts but distinguished by the model's structure.
  - **Safety**: "Thoughts" are generally for the model's internal process, but `include_thoughts=True` exposes them.

## Action Items for Visions AI

1. **Code Execution**: Ensure `display_code_execution_result` logic is adapted for our Agent UI (we need to parse `executable_code` parts).
2. **Search**: We must capture and log `grounding_metadata` for attribution compliance.
3. **File Search**: Implement `KnowledgeRetriever` to potentially use `FileSearch` API instead of just FAISS if scaling is needed (currently FAISS is fine, but File Search is "Gemini Native").
4. **Parallel Tools**: Verify `VisionsAgent` handles a list of function calls in one response (loop through `part.function_call` if multiple parts exist).

## 6. Spatial Understanding (`spatial_understanding.py`, `spatial_understanding_3d.py`)

### 2D Spatial Understanding

- **Models**: `gemini-3-flash-preview` (fast), `gemini-2.5-pro` (better).
- **Standard Output**: JSON array with `box_2d` and `label`.
- **Coordinates**: Normalized `[0-1000]`. **Order: `[ymin, xmin, ymax, xmax]`** (Note Y first).
- **System Instruction**:

  ```python
  bounding_box_system_instructions = """
    Return bounding boxes as a JSON array with labels. Never return masks or code fencing. Limit to 25 objects.
  """
  ```

- **Segmentation** (Gemini 2.5 only): Can return base64 PNG masks in `mask` field.

### 3D Spatial Understanding (Experimental)

- **Capabilities**:
  1. **Pointing**: `[y, x]` coordinates (0-1000). Useful for "Point to X".
  2. **3D Bounding Boxes**: `[x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw]`.
  3. **Multiview Correspondence**: Identify points in one image and find them in another angle.
- **Prompting**:

  ```text
  Detect the 3D bounding boxes... Output a json list... 
  The 3D bounding box format should be [x_center, y_center, z_center, x_size, y_size, z_size, roll, pitch, yaw].
  ```

### Updated Action Items

1. **Spatial Parsing**: Add a utility to parse and visualize 2D/3D tokens (e.g., `ymin, xmin, ymax, xmax` to `x,y,w,h` for UI).
2. **Safety**: Use `RunSafetyCheck` if using `gemini-3-flash-preview` for spatial understanding to ensure no PII is inadvertently boxed/labeled.

## 7. Basic Context Injection (`prompting/adding_context_information.py`)

- **Concept**: Simply concatenating `QUERY: ...` and `CONTEXT: ...` in the prompt is the baseline for RAG/Knowledge injection.
- **Pattern**:

  ```python
  prompt = f"""
    QUERY: {user_query}
    CONTEXT:
    {retrieved_data}
  """
  ```

- **Note**: For large context, prefer **Context Caching** or **File Search** (Section 4) over this raw string concatenation method to save input tokens/latency.

## 8. Video Understanding

**Source**: `analyze_a_video_*.py`

- **Workflow**:
  1. **Upload**: `video_file = client.files.upload(file=path)`.
  2. **Wait**: You **MUST** poll while `video_file.state.name == "PROCESSING"`.
  3. **Inference**: Pass `video_file` in `contents`.
  4. **Cleanup**: `client.files.delete(name=video_file.name)`.
- **Framerate**: Gemini samples **1 FPS**. Short/fast actions might be missed.
- **Historic Content**: For historical/political content, you may need to relax safety settings (`BLOCK_NONE`).
- **Models**: `gemini-3-flash-preview` is the standard for fast video analysis.

## 9. Asynchronous Requests (`quickstarts/asynchronous_requests.py`)

- **Namespace**: Access async methods via `client.aio`.
  - **Sync**: `client.models.generate_content(...)`
  - **Async**: `await client.aio.models.generate_content(...)`
- **Parallelism**: Use `asyncio.gather(*tasks)` to run multiple independent requests concurrently (e.g., processing 10 images at once).
- **Critical For Agents**: Ensure `VisionsAgent` uses `client.aio` methods inside `async def` functions to avoid blocking the event loop.

## 10. Prompting Patterns (`prompting/*.py`)

- **Basic Code Gen**:
  - Use `temperature=0` for deterministic code.
  - Manual extracting: `re.search(r"python\n(.*?)```", response.text)` (Note: The `code_execution` tool is preferred for running code).
- **Chain of Thought (CoT)**:
  - **Manual CoT**: For models without native thinking (or to force specific logic paths), use few-shot prompting with "Question: ... Answer: Step 1, Step 2..." format.
  - **Native Thinking**: For Gemini 3 `thinking_level="HIGH"` is preferred over manual CoT for complex reasoning.
- **Few-Shot Prompting (`few_shot_prompting.py`)**:
  - Provide examples in the prompt to define output format or logic.
  - Example: `Question: Sort A,B. Answer: B>A` -> `Question: Sort C,D. Answer:`
  - Combine with JSON mode (`response_mime_type="application/json"`) for structured extraction.

## 11. Embeddings (`embeddings.py`)

- **Model**: `gemini-embedding-001` or `text-embedding-004`.
- **Task Types**: Critical for RAG accuracy.
  - `RETRIEVAL_QUERY`: For the user's question.
  - `RETRIEVAL_DOCUMENT`: For the corpus during indexing.
  - `SEMANTIC_SIMILARITY`: For comparing two texts.
- **Dimensionality**: customizable (e.g., truncate to save storage).
- **Batching**: Supports batch inputs in `client.models.embed_content(contents=[...])`.

## 12. Structured Output & JSON Mode (`json_mode.py`)

- **Key Config**: `response_mime_type="application/json"`.
- **Implicit Schema**: Describe schema in prompt (e.g., "Return a list of: ...").
- **Explicit Schema (Gold Standard)**: Pass a Python type to `response_schema`.

  ```python
  class Recipe(typing.TypedDict):
      name: str
      ingredients: list[str]

  config = types.GenerateContentConfig(
      response_mime_type="application/json",
      response_schema=list[Recipe]
  )
  ```

- **Result**: `response.parsed` provides the direct Python object (list/dict), avoiding manual `json.loads`.

### 12.1 Text Classification & Enums (`text_classification.py`)

- **Enums**: Use `enum.Enum` to constrain values strictly.

  ```python
  class Relevance(enum.Enum):
      WEAK = "weak"
      STRONG = "strong"
  ```

- **Usage**: Include the Enum in your `TypedDict` schema.

### 12.2 Structured Summarization (`text_summarization.py`)

- **Pattern**: Extract richer data than just a text blob.

  ```python
  class TextSummary(TypedDict):
      synopsis: str
      genres: list[str]
      characters: list[Character]
  ```

## 13. File Search Details (`file_search.py`)

- **Indexing**:
  - Create Store: `client.file_search_stores.create(...)`
  - Upload: `client.file_search_stores.upload_to_file_search_store(...)` (or import via File API).
- **Querying**:

  ```python
  tools=[types.Tool(file_search=types.FileSearch(
      file_search_store_names=[store.name],
      metadata_filter='genre = "fiction"' # Metadata filtering supported
  ))]
  ```

- **Attribution**: ALWAYS render `grounding_metadata.grounding_supports` as superscripts/tooltips.

## 14. Context Caching (`caching.py`)

- **Cost/Latency**: Massive savings for large, repeated contexts (e.g., full books, codebases).
- **Workflow**:
  1. **Create**: `cache = client.caches.create(model=..., config={'contents': [doc], 'ttl': '7200s'})`.
  2. **Use**: `client.models.generate_content(..., config={'cached_content': cache.name})`.
  3. **Update TTL**: `client.caches.update(name=cache.name, config={'ttl': '...'})`.
- **Note**: Caches are model-specific!

## 15. Audio Understanding (`audio.py`)

- **Input**:
  - **File API**: `contents=[audio_file]` (Best for long audio).
  - **Inline**: `types.Part.from_bytes(data=..., mime_type='audio/mp3')` (Max 20MB).
- **Features**:
  - **Timestamps**: Can ask "Summarize 02:30-03:29".
  - **Transcripts**: "Generate a transcript" is a native capability.

## 16. Vector Search & Recommendations (`movie_recommendation.py`)

- **Pattern**: Generate embeddings -> Store in Vector DB (Qdrant/Chroma) -> Query with Cosine Similarity.
- **Batched Embeddings**: Use retry logic for robustness when embedding large datasets.

## 17. Image Tagging & Visual Search (`tag_and_caption_images.py`)

- **Tagging**: Prompt with allowed keyworks list + Image.
- **Correction**: Use Embeddings to map "fuzzy" generated tags to canonical tags (e.g., "denim" -> "jeans") using cosine similarity.
- **Search**: Convert (Keywords + Caption) to embedding, then search against database of image embeddings.

## 18. System Instructions (REST API) (`system_instructions_rest.py`)

- **JSON Field**: `system_instruction` (Singular).
- **Structure**:

  ```json
  {
    "system_instruction": {
      "parts": { "text": "You are a helpful assistant..." }
    }
  }
  ```

- **SDK Equivalent**: `types.GenerateContentConfig(system_instruction=...)`.

## 19. Self-Ask Prompting (`self_ask_prompting.py`)

- **Concept**: Explicitly decomposing queries into sub-questions ("Follow up") and "Intermediate answers" before the "Final answer".
- **Pattern**:

  ```text
  Question: Who was president when Mozart died?
  Are follow up questions needed?: yes.
  Follow up: When did Mozart die?
  Intermediate answer: 1791.
  Follow up: Who was president in 1791?
  Intermediate answer: George Washington.
  Final answer: ...
  ```

- **Gemini 3 Synergy**:
  - Works well with **Function Calling** (using follow-ups as tool queries).
  - Can be replaced/automated by **Thinking Models** (`thinking_level="HIGH"`) which natively perform this decomposition.

## 20. Zero-Shot Prompting (`zero_shot_prompting.py`)

- **Concept**: Baseline capability to perform tasks (Sort, Classify, Extract, Fix Code, Math) with instructions but *zero* examples.
- **Use Case**: Default mode for general queries or simple tasks.
- **Contrast**: Use **Few-Shot** (Section 11) for complex formatting or style mimicry; use **Thinking** for complex reasoning.

## 21. Anomaly Detection (`anomaly_detection.py`)

- **Concept**: Using Embeddings to detect semantic outliers in a dataset.
- **Workflow**:
  1. Generate Embeddings for all items (Task Type: `CLUSTERING`).
  2. Group items by Category/Label.
  3. Calculate **Centroid** (Mean vector) for each category.
  4. Calculate **Euclidean Distance** of each item to its category centroid.
  5. Items with `distance > RADIUS` (threshold, e.g., 0.54) are outliers.
- **Key Code**:

  ```python
  def detect_outlier(df, centroids, radius):
      for idx, row in df.iterrows():
          dist = np.linalg.norm(row['Embeddings'] - centroids[row['Class']])
          if dist > radius: mark_outlier(row)
  ```
