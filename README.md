# 🎨 Visions AI

<div align="center">

![Visions AI](https://img.shields.io/badge/Visions-AI-purple?style=for-the-badge&logo=google&logoColor=white)
![Gemini 3](https://img.shields.io/badge/Gemini%203-Pro-blue?style=for-the-badge)
![Vertex AI](https://img.shields.io/badge/Vertex-AI-orange?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.12-green?style=for-the-badge&logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**🌟 A World-Class Photography AI Mentor Powered by Google's Latest Models 🌟**

*80 Years of Visual Arts Experience • Gemini 3 Pro Synthesis • Cloud Memory System*

[![Instagram](https://img.shields.io/badge/Instagram-@aiwithdav3-E4405F?style=flat-square&logo=instagram&logoColor=white)](https://instagram.com/aiwithdav3)
[![YouTube](https://img.shields.io/badge/YouTube-@aiwithdav3-FF0000?style=flat-square&logo=youtube&logoColor=white)](https://youtube.com/aiwithdav3)
[![Website](https://img.shields.io/badge/Website-whovisions.com-4285F4?style=flat-square&logo=google-chrome&logoColor=white)](https://whovisions.com)

</div>

---

## ✨ What is Visions?

**Visions** is an advanced AI photography mentor and creative director built on Google Cloud's Vertex AI platform. It combines the power of multiple Gemini models with **async cloud memory** to provide personalized, expert-level guidance.

### 🎯 Core Capabilities

| Feature | Description |
|---------|-------------|
| 📸 **Photography Techniques** | Composition, lighting, camera settings |
| 🎥 **Cinematic Direction** | Framing, color grading, visual storytelling |
| 📷 **Camera Equipment** | Recommendations for Canon, Sony, Leica, Phase One |
| 🖼️ **Image Analysis** | Critique your work with actionable feedback |
| 🎨 **Image Generation** | Create visuals with Gemini 3 Pro Image Preview |
| 🧠 **Persistent Memory** | Remembers your preferences across sessions |

---

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

---

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

### 📡 Model Routing

| Model | Location | Purpose |
|-------|----------|---------|
| `gemini-3-pro-preview` | 🌍 Global | Final synthesis & response |
| `gemini-2.5-flash-lite` | 📍 us-central1 | Query triage & quick instinct |
| `gemini-2.5-flash` | 📍 us-central1 | Grounded search (real-time data) |
| `gemini-2.5-pro` | 📍 us-central1 | Deep thinking & analysis |
| `gemini-3-pro-image-preview` | 🌍 Global | Native image generation |

---

## 🏗️ Architecture

### ☁️ Vertex AI Reasoning Engine

Visions is deployed as a **Reasoning Engine** on Google Cloud:

- ⚡ **Low-latency inference** - Optimized endpoints
- 🔄 **Automatic scaling** - Handles traffic spikes
- 🔒 **Enterprise security** - IAM integration
- 📊 **Usage monitoring** - Built-in analytics
- 🧠 **Cloud memory** - Firestore + BigQuery

### 📁 Project Structure

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

---

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

---

## 🛠️ Commands

| Command | Description |
|---------|-------------|
| `/generate <prompt>` | Generate image with aspect ratio selector |
| `/image <path> <prompt>` | Analyze uploaded image |
| `/memory` | View memory statistics |
| `/stats` | System performance stats |
| `/help` | Show all commands |
| `/exit` | Terminate session |

---

## 🚢 Deployment

### Reasoning Engine (Vertex AI)

```bash
python deploy.py
```

### Cloud Run (via GitHub)

Push to `main` branch triggers automatic deployment via Cloud Build.

---

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `VERTEX_PROJECT_ID` | GCP Project ID |
| `VERTEX_LOCATION` | Region (default: us-central1) |
| `REASONING_ENGINE_ID` | Deployed engine ID |
| `GOOGLE_AI_STUDIO_API_KEY` | Fallback API key |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with 💜 by [Who Visions LLC](https://whovisions.com)**

*Powered by Google Cloud Vertex AI & Gemini*

---

### 🌟 Connect with Us

[![Instagram](https://img.shields.io/badge/Instagram-E4405F?style=for-the-badge&logo=instagram&logoColor=white)](https://instagram.com/aiwithdav3)
[![YouTube](https://img.shields.io/badge/YouTube-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtube.com/aiwithdav3)
[![Website](https://img.shields.io/badge/WhoVisions.com-4285F4?style=for-the-badge&logo=google-chrome&logoColor=white)](https://whovisions.com)

</div>
