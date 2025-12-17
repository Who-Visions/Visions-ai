# How to Run Ingestion Scripts

You encountered an error because you were trying to run the script from *inside* the Python interpreter (`>>>`).

## Correct Steps

1. **Exit Python**:
   - Type `exit()` and press Enter.
   - OR press `Ctrl+Z` then Enter.
   - You should see the standard prompt (e.g., `PS C:\Users\super...`).

2. **Run the Video Ingestion**:
   ```powershell
   python scripts/ingest_youtube.py
   ```
   *This will take some time as it processes 100+ videos.*

3. **Run the Indexer**:
   ```powershell
   python build_index.py
   ```
   *This compiles the new transcripts into the agent's memory.*

## Troubleshooting
- If you see `NameError`, you are still in Python.
- If you see `command not found`, ensure you are in the `Visions-ai` directory.
