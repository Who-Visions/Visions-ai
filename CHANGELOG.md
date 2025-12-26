# Changelog

All notable changes to the `Visions-ai` project will be documented in this file.

## [Unreleased] - 2025-12-26

### Added

- **Gemini 3 Integration**: Full support for `gemini-3-pro-preview` and `gemini-3-flash-preview` across the agent.
- **Deep Research Agent**: Integrated specialized agent mechanism via `visions/skills/deep_research/`.
- **Level 3 Skill Execution**: Added `run_skill_program` to `VisionsAgent` to execute local python scripts as tools.
- **Cookbook Patterns**:
  - **Structured Output**: Implemented JSON Mode in `_triage_query`.
  - **Multimodal Inputs**: Added Audio/Video/Image support to `VisionsAgent.query`.
  - **Context Caching**: Added `visions/modules/caching.py` for managing long-context caches.
  - **Vision Tools**: Added `tag_image` with embedding-based correction, `visual_question_answer`, `generate_json_prompt`.
  - **Prompting Patterns**: Added support for Zero-Shot, Self-Ask, Chain of Thought, and Few-Shot strategies.
  - **Anomaly Detection**: Documented pattern for embedding-based outlier detection.

### Changed

- **Config**: Centralized all model constants in `visions/core/config.py`. Deprecated legacy model strings.
- **Routing**: `VisionsAgent` now uses a smart cascade (Flash-Lite -> Flash -> Pro) with native JSON routing.
- **Cost Tracking**: Updated `cost_tracker.py` to support Gemini 3 pricing tiers.

### Fixed

- **Response Parsing**: Fixed regex fragility by moving to `response_mime_type="application/json"`.
- **Imports**: Resolved import path issues for `VisionTools`.
