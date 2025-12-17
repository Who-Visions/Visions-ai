# Visions AI Agent Configuration

This repository contains the source code for **Visions AI**, a multi-agent system designed for content creation, research, and coding assistance.

## Agents & Tools

### Browser Tool (`tools/browser_tool.py`)
- **Purpose**: Allows agents to control a Chrome browser to navigate, click, and extract content from websites.
- **Underlying Tech**: Uses `chrome-devtools-mcp` via `npx` and a custom MCP Client (`tools/mcp_client.py`).
- **Usage**:
  ```python
  from tools.browser_tool import BrowserTool
  browser = BrowserTool()
  browser.navigate("https://example.com")
  content = browser.get_content()
  ```

### Memory System
- **Location**: `memory.py`, `memory_cloud.py`
- **Purpose**: Stores and retrieves long-term memory using Firestore/Vector stores.

## Development Workflow
- **Language**: Python 3.x
- **Testing**: Run tests using `python tests/test_name.py`.
- **Linting**: Standard Python practices.

## Key Directories
- `tools/`: Contains all agent tools (Browser, Search, etc.).
- `knowledge_base/`: Markdown files containing project knowledge and context.
- `tests/`: Unit and integration tests.
