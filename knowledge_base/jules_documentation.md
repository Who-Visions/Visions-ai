# Jules Agent Knowledge Base

## Overview
Jules is Google's autonomous AI coding agent designed to fix bugs, add documentation, and build features. It integrates with GitHub and runs in a virtual machine.

## Getting Started
1.  **Login**: `jules login` or visit jules.google.com.
2.  **Connect GitHub**: Authorize access to repositories.
3.  **AGENTS.md**: Place this file in the root to describe tools/agents. structure is crucial for context.

## Usage
- **Web UI**: jules.google.com
- **CLI**: `jules` command (TUI available).
- **Remote Sessions**: `jules remote new --session "fix bug"`
- **Authentication**: `jules login`

## Environment Setup
Jules runs in a VM based on Ubuntu.
- **Preinstalled**: node, npm, python3, pip, git, gh, curl, wget.
- **Setup Script**: Can provide a script to run before the task starts (e.g., `npm install`, `pip install -r requirements.txt`).
- **Snapshots**: Jules snapshots the environment after setup to speed up subsequent tasks.
- **Validation**: Ensure scripts are non-interactive (`npm install -y`) and idempotent.

## Running Tasks
- **Prompting**: Be specific, plain language. Can attach images (PNG/JPEG < 5MB) for context (ui mocks, errors).
- **Process**:
    1. Select Repo & Branch.
    2. Write Prompt (e.g., "Add loading spinner").
    3. **Plan Review**: Jules generates a plan. You must review and approve it.
    4. **Execution**: Jules clones, installs, modifies code. You can watch live diffs.
    5. **Feedback**: Can interrupt/pause and provide feedback mid-task.
    6. **Completion**: Review summary, create branch/PR.
- **GitHub Integration**: Can trigger via issue label `jules`.

## Reviewing Plans
- **Importance**: Review the generated plan before code execution.
- **Feedback**: If the plan is wrong, ask Jules to revise it before approving.
- **Controls**: Pause/Resume/Delete tasks.
