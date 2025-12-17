# Analysis: Agent Experts & Meta-Agentics
**Source:** [(85) Agent Experts: WHAT IF Your Claude Code Agents could LEARN? - YouTube](https://www.youtube.com/watch?v=zTcDwqopvKE)
**Video ID:** `zTcDwqopvKE`

## Core Problem
**Agents Forget.**
- Traditional agents execute tasks and then reset. They do not retain learnings from previous runs.
- **Consequences:** You have to manually update prompts, context files, and memory files.
- **Solution:** "Agent Experts" that learn at runtime.

## Key Concepts

### 1. The Agent Expert
- **Definition:** An agent that acts, learns, and reuses expertise. It doesn't just execute; it updates its own mental model.
- **Mechanism:**
    1.  **Read Expertise:** Reads a dedicated "Expertise File" (Mental Model) at the start of a task.
    2.  **Validate:** Compares its mental model against the actual codebase (Source of Truth).
    3.  **Execute:** Performs the task.
    4.  **Self-Improve:** Updates the "Expertise File" with new findings/patterns (e.g., adding a new database table to the schema map in its memory).

### 2. The Expertise File (Mental Model)
- **Format:** YAML or Markdown file.
- **Purpose:** A structured "working memory" for the agent.
- **Distinction:**
    - **Source of Truth:** The Codebase (always).
    - **Mental Model:** The Expertise File (a map/understanding of the code).
- **Example:** A `database_expert.yaml` file containing an entity relationship diagram and data flow notes.

### 3. Meta-Agentics
"The system that builds the system."
- **Meta-Prompts:** Prompts that write other prompts (e.g., a prompt that generates a specialized "Question Prompt").
- **Meta-Agents:** Agents that spin up other agents (e.g., a "Builder Agent" spinning up 3 "Websocket Experts").
- **Meta-Skills:** Skills that create other skills.

## Architecture Pattern
1.  **Workflow:** Plan -> Build -> **Self-Improve**.
2.  **Self-Improve Step:** This is the critical missing piece in most agent loops. After the work is done, run a "Self-Improve Prompt" that looks at what changed (using `git diff` or similar) and updates the relevant `expertise.yaml` file.

## Strategic Relevance (Visions AI)
- **Alignment:** This fits perfectly with **Gemini 3.0's Active Working Memory**. We can treat the "Expertise File" as a persistent artifact that feeds into Gemini's context.
- **Antigravity:** We should implement "Meta-Agentics" in our `task.md` workflow (e.g., a task to update specific memory files after a coding session).
- **Google Ecosystem:** Use **Gemini 3.0** to generate and maintain these expertise files.
