# 🎨 Visions AI

<div align="center">

![Visions AI](https://img.shields.io/badge/Visions-AI-purple?style=for-the-badge&logo=google&logoColor=white)
![Gemini 3](https://img.shields.io/badge/Gemini%203-Pro-blue?style=for-the-badge)
![Vertex AI](https://img.shields.io/badge/Vertex-AI-orange?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)

**A World-Class Photography AI Mentor Powered by Google's Latest Models**

*80 Years of Visual Arts Experience • Gemini 3 Pro Synthesis • Multi-Model Intelligence Cascade*

</div>

---

## ✨ What is Visions?

**Visions** is an advanced AI photography mentor and creative director built on Google Cloud's Vertex AI platform. It combines the power of multiple Gemini models in an intelligent cascade to provide expert-level guidance on:

- 📸 **Photography Techniques** - Composition, lighting, camera settings
- 🎥 **Cinematic Direction** - Framing, color grading, visual storytelling
- 📷 **Camera Equipment** - Recommendations for Canon, Sony, Leica, Phase One
- 🖼️ **Image Analysis** - Critique your work with actionable feedback
- 🎨 **Image Generation** - Create visuals with Imagen 4

---

## 🧠 Smart Model Cascade

Visions uses an **intelligent multi-model architecture** that routes queries to the optimal AI model:

```
┌─────────────────────────────────────────────────────────────┐
│                      USER QUERY                              │
└─────────────────────────────┬───────────────────────────────┘
                              │
                   ┌──────────▼──────────┐
                   │  🎯 TRIAGE          │
                   │  (Flash-Lite)       │
                   │  Analyze Intent     │
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
| `gemini-3-pro-preview` | 🌍 Global | Final synthesis & response |
| `gemini-2.5-flash-lite` | 📍 us-central1 | Query triage & quick instinct |
| `gemini-2.5-flash` | 📍 us-central1 | Grounded search (real-time data) |
| `gemini-2.5-pro` | 📍 us-central1 | Deep thinking & analysis |
| `imagen-4.0-generate-001` | 📍 us-central1 | Image generation |

---

## 🚀 Features

### 🎯 Smart Query Routing
Flash-Lite analyzes every query to determine which models are needed:
- **Greetings** → Skip heavy models, respond instantly
- **Latest cameras** → Grounded search for real-time data
- **Complex analysis** → Deep thinking with Pro
- **Photography theory** → RAG knowledge base

### 📡 Real-Time Output
See results stream as each model completes:
```
🧠 Cascading thought process initiated...
────────────────────────────────────────────
   ⚡ Flash-Lite: Quick assessment
   🌐 Flash: Grounded search
   🔮 Pro: Deep thinking
   📚 RAG: Knowledge base
────────────────────────────────────────────
📡 REAL-TIME OUTPUT:
   ✓ INSTINCT complete
   ✓ GROUNDED complete
   ✓ THINKING complete
────────────────────────────────────────────
✅ 3 pathways complete → Synthesizing...
```

### 🔤 Intelligent Typo Correction
Visions silently corrects common typos:
- `Cannon` → Canon
- `Somy` → Sony
- `Nikkon` → Nikon

### 🗣️ Contextual Understanding
Uses conversation history to understand follow-up questions without asking for clarification.

---

## 📁 Project Structure

```
Visions-ai/
├── 🧠 agent.py              # Core agent with cascade logic
├── 🎨 animations.py         # Rich visual feedback
├── 💻 cli.py                # Basic CLI
├── ✨ cli_visual.py         # Ultra-visual CLI with emojis
├── 🧪 cli_enhanced.py       # Memory-enhanced CLI
├── 💾 memory.py             # Short & long-term memory
├── 🚀 visions_visual.bat    # Windows launcher
├── 📚 tools/
│   ├── vision_tools.py      # Gemini 3 vision capabilities
│   ├── youtube_tools.py     # Video analysis
│   └── cinema_tools.py      # Cinematic generation
└── 📖 docs/
    └── QUOTA_MANAGEMENT.md
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

**Windows (Recommended):**
```batch
visions_visual.bat
```

**Linux/WSL:**
```bash
python cli_visual.py
```

---

## 💎 CLI Preview

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              ✨ V I S I O N S   A I ✨                        ║
║                                                               ║
║  ╭──────────────╮ ╭──────────────╮ ╭──────────────╮          ║
║  │ 🌍 Global    │ │ 🚀 Active    │ │ 🧠 Online    │          ║
║  │ Vertex AI    │ │ AI Studio   │ │ Memory       │          ║
║  ╰──────────────╯ ╰──────────────╯ ╰──────────────╯          ║
║                                                               ║
╚══════════════════ 💎 v3.0 | Smart Routing ═══════════════════╝

🚀 Initializing Neural Link...
🔑 Authenticating Identity...
🧠 Loading Memory Systems...
💾 Short-Term Memory... ✅
☁️ Long-Term Database... ✅
⚡ Cascade Router... ✅
🔥 System Ready!

📸 Input: What's the best camera for street photography?
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

## 🏗️ Architecture

### Vertex AI Reasoning Engine
Visions is deployed as a **Reasoning Engine** on Google Cloud, enabling:
- ⚡ Low-latency inference
- 🔄 Automatic scaling
- 🔒 Enterprise security
- 📊 Usage monitoring

### Memory System
- **Short-term**: 100 entries per session (RAM)
- **Long-term**: SQLite database (Persistent)
- **Future**: BigQuery analytics sync

---

## 📊 Model Capabilities

### Gemini 3 Pro Preview
- ✅ Advanced reasoning
- ✅ Multi-turn conversations
- ✅ System instructions
- ✅ Visual understanding

### Imagen 4
- ✅ Text-to-image generation
- ✅ Multiple aspect ratios (1:1, 16:9, 9:16, 4:3, 3:4)
- ✅ High resolution (up to 2816x1536)
- ✅ Multi-language prompts

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

<div align="center">

**Built with 💜 by [WhoArt](https://github.com/Who-Visions)**

*Powered by Google Cloud Vertex AI & Gemini*

</div>
