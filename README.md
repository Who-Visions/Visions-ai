<!-- nougen-readme-compiler: v1 -->

<!-- nougen-readme-compiler: extensions: footer -->

# 🎨 Visions AI

A world-class photography AI mentor powered by Google's latest models — 80 years of visual arts experience, Gemini 3 Pro synthesis, and a cloud memory system.

![Visions AI](<https://img.shields.io/badge/Visions-AI-purple?style=for-the-badge&logo=google&logoColor=white>) ![Gemini 3](<https://img.shields.io/badge/Gemini%203-Pro-blue?style=for-the-badge>) ![Vertex AI](<https://img.shields.io/badge/Vertex-AI-orange?style=for-the-badge>) ![Python 3.12](<https://img.shields.io/badge/Python-3.12-green?style=for-the-badge&logo=python&logoColor=white>) ![Status Active](<https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge>)

## 📚 Contents
- [What is Visions](#what-is-visions)
- [Memory Architecture](#memory-architecture)
- [Smart Model Cascade](#smart-model-cascade)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Commands](#commands)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [Working on this repo from more than one machine](#working-on-this-repo-from-more-than-one-machine)
- [Contributing](#contributing)
- [License](#license)

## ✨ What is Visions

**Visions** is an advanced AI photography mentor and creative director built on Google Cloud's Vertex AI platform. It combines the power of multiple Gemini models with **async cloud memory** to provide personalized, expert-level guidance.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 📸 **Photography Techniques** | Composition, lighting, camera settings |
| 🎥 **Cinematic Direction** | Framing, color grading, visual storytelling |
| 📷 **Camera Equipment** | Recommendations for Canon, Sony, Leica, Phase One |
| 🖼️ **Image Analysis** | Critique your work with actionable feedback |
| 🎨 **Image Generation** | Create visuals with Gemini 3 Pro Image Preview |
| 🧠 **Persistent Memory** | Remembers your preferences across sessions |

## 🧠 Memory Architecture

Visions uses a **dual-layer cloud memory system** for personalized interactions:

```
┌─────────────────────────────────────────────────────────────┐
│                     VISIONS AI MEMORY                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ⚡ SHORT-TERM (Firestore)           🧠 LONG-TERM (BigQuery) │
│  ├── Session messages                ├── User preferences    │
│  ├── Current context                 ├── Conversation history│
│  └── Real-time sync                  └── Semantic search     │
│                                                              │
│  💾 FALLBACK (SQLite)                                        │
│  └── Works offline/local development                         │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Auto-persists important info like:**
- "My name is..." → `user:name`
- "I prefer..." → `preference:general`
- "I work at..." → `user:occupation`

## 🚀 Smart Model Cascade

Visions uses an **intelligent multi-model architecture** that routes queries to the optimal AI model:

```
                    ┌──────────────────────┐
                    │     USER QUERY       │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼──────────┐
                    │  🎯 TRIAGE          │
                    │  (Flash-Lite)       │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
    ┌────▼────┐          ┌─────▼─────┐         ┌─────▼─────┐
    │   🌐    │          │    🔮     │         │    📚     │
    │  Flash  │          │   Pro     │         │   RAG     │
    │Grounded │          │ Thinking  │         │ Knowledge │
    └────┬────┘          └─────┬─────┘         └─────┬─────┘
         │                     │                     │
         └─────────────────────┼─────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  🧠 GEMINI 3 PRO    │
                    │  Final Synthesis    │
                    └─────────────────────┘
```

### Model Routing

| Model | Location | Purpose |
|-------|----------|---------|
| `gemini-3.1-pro-preview` | 🌍 Global | Final synthesis & response |
| `gemini-3.1-flash-lite` | 📍 us-central1 | Query triage & quick instinct |
| `gemini-3.6-flash` | 📍 us-central1 | Grounded search (real-time data) |
| `gemini-3.1-pro-preview` | 📍 us-central1 | Deep thinking & analysis |
| `gemini-3-pro-image` | 🌍 Global | Native image generation |

## 🏗️ Architecture

### Vertex AI Reasoning Engine

Visions is deployed as a **Reasoning Engine** on Google Cloud:

- ⚡ **Low-latency inference** - Optimized endpoints
- 🔄 **Automatic scaling** - Handles traffic spikes
- 🔒 **Enterprise security** - IAM integration
- 📊 **Usage monitoring** - Built-in analytics
- 🧠 **Cloud memory** - Firestore + BigQuery

### Project Structure

```
Visions-ai/
├── 🧠 agent.py              # Core agent with cascade logic + memory
├── 💾 memory_cloud.py       # Cloud memory (Firestore + BigQuery)
├── ⚙️ config.py             # Configuration & environment
├── 🚀 deploy.py             # Reasoning Engine deployment
├── 🐳 Dockerfile            # Cloud Run container (Python 3.12)
├── 🔧 cloudbuild.yaml       # CI/CD pipeline
├── 📚 tools/
│   ├── vision_tools.py      # Gemini 3 vision capabilities
│   ├── youtube_tools.py     # Video analysis
│   ├── cinema_tools.py      # Cinematic generation
│   └── agent_connect.py     # Inter-agent communication
└── 🧪 tests/                # Test suite
```

## 🎮 Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud Project with Vertex AI enabled
- `gcloud` CLI authenticated

### Installation

```bash
# Clone the repository
git clone git@github.com:Who-Visions/Visions-ai.git
cd Visions-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up authentication
gcloud auth application-default login
```

### Run Visions

**Windows:**
```batch
visions_visual.bat
```

**Linux/WSL:**
```bash
python cli_visual.py
```

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `/generate <prompt>` | Generate image with aspect ratio selector |
| `/image <path> <prompt>` | Analyze uploaded image |
| `/memory` | View memory statistics |
| `/stats` | System performance stats |
| `/help` | Show all commands |
| `/exit` | Terminate session |

## 🚢 Deployment

### Reasoning Engine (Vertex AI)

```bash
python deploy.py
```

### Cloud Run (via GitHub)

Push to `main` branch triggers automatic deployment via Cloud Build.

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `VERTEX_PROJECT_ID` | GCP Project ID |
| `VERTEX_LOCATION` | Region (default: us-central1) |
| `REASONING_ENGINE_ID` | Deployed engine ID |
| `GOOGLE_AI_STUDIO_API_KEY` | Fallback API key |

## 🔄 Working on this repo from more than one machine

This repo is worked from several boxes. Announce before you start:

```bash
relay check                                   # has another machine moved?
relay claim take -s visions/core -g "what you are doing"
# ... work ...
relay claim release -s visions/core
relay create -g "what you did" -m "where you left off"
```

Records land in `.handoffs/`. Install the CLI from [NouGenRelay](https://github.com/who-visions/nougenrelay); if `relay` is not on PATH after `pip install -e .`, `python -m nougen_relay` always works.

**Commits carry their origin.** `.githooks/prepare-commit-msg` stamps every commit with `Machine:` and `Agent:` trailers, so `git log` answers "which box, which lane" rather than only "which GitHub account":

```bash
git config core.hooksPath .githooks
```

That is per-clone — `core.hooksPath` lives in `.git/config` and cannot be committed — so a fresh clone starts unstamped until someone runs it.

### Why this exists

Until 2026-08-02 this repo had no registry at all, and it cost something specific. A GCP project move and a Gemini version bump sat uncommitted in a working tree for months, hidden under 285 files of mode-only churn (`100644 -> 100755` on everything, including `.gitignore`). In the same tree `visions/core/agent.py` carried two syntax errors and could not be imported, and `main` held 36 references to Gemini models Google had already shut down.

None of that was announced anywhere, because nothing was watching. Set `core.fileMode false` if you see phantom modifications — that noise is what kept the real diff invisible.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Instagram](<https://instagram.com/aiwithdav3>)
- [YouTube](<https://youtube.com/aiwithdav3>)
- [Website](<https://whovisions.com>)
- [Source Repository](<https://github.com/Who-Visions/Visions-ai>)

Built with 💜 by Who Visions LLC — Powered by Google Cloud Vertex AI & Gemini
