---
name: deep_research
description: Conducts rigorous academic research and document analysis using Gemini's advanced control features (Logprobs, Citations, Long Context).
usage_trigger: Use when the user asks for "research", "paper analysis", "fact checking", "academic review", or "uncertainty analysis".
---

# 🔬 Deep Research Skill

## Capabilities

This skill leverages specific **Gemini Research** features to provide higher-fidelity analysis than standard chat.

1. **Uncertainty Quantification (Logprobs)**:
    * When analyzing complex topics, this skill checks the `logprobs` of the generated tokens.
    * It highlights statements where the model's confidence is low, preventing hallucinations.

2. **Rigorous Citations (CitationMetadata)**:
    * Enforces strict citation extraction using `groundingMetadata`.

3. **Long-Context Synthesis**:
    * Optimized for ingesting full PDF papers or large text dumps (up to 2M tokens).

## Instructions

### For Paper Analysis

1. **Ingest**: Read the full content of the file.
2. **Analyze**: Use the configured Pro model (currently `gemini-3-pro-preview`) with `thinking_level="HIGH"`.
3. **Output**: structured report with:
    * **Core Thesis**: What is the paper claiming?
    * **Methodology Evaluation**: Is it sound?
    * **Confidence Score**: Based on Logprobs (simulated or actual if access permits).
    * **Novelty Assessment**: How does this comparing to existing literature?

### For Fact Checking

1. Activate `google_search` tool.
2. Cross-reference claims.
3. Explicitly list `CitationMetadata` sources.

## Python Helper (Concept)

Use `visions/core/visions_backend.py` to access the raw client if you need to inspect `response.candidates[0].logprobs`.
