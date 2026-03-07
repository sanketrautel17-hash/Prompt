# 🎙️ VoicePrompt AI

> Speak your idea. Get a perfectly-structured AI prompt. Injected instantly.

VoicePrompt AI is a Wispr Flow-style Windows desktop utility that listens to your voice, transcribes it, detects your intent, and uses an LLM to transform your rough idea into a beautifully-structured AI prompt — copied straight to where your cursor is.

---

## ✨ Features

| Feature | Detail |
|---------|--------|
| 🎤 **Push-to-talk** | Hold `Ctrl+Space` to record, release to process |
| 🧠 **5 Prompt Frameworks** | CO-STAR · ROSES · RFGF · Tree of Thoughts · Chain of Thought |
| ⚡ **Auto-inject** | Prompt is pasted directly into your active window |
| 🌍 **Multi-language** | English · Hindi · Marathi |
| 📜 **History** | Every prompt saved to MongoDB; browse via API |
| 🔒 **Private** | Audio is never stored to disk |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│  Desktop App (PyQt6)                                 │
│                                                      │
│  Ctrl+Space  →  AudioRecorder  →  POST /voice/process│
│                                        │             │
│  OverlayWidget ← QThread Worker ←──────┘             │
│  TextInjector ← generated_prompt                    │
└─────────────────────────────────────────────────────┘
                          │  HTTP
┌─────────────────────────────────────────────────────┐
│  FastAPI Backend                                     │
│                                                      │
│  POST /voice/process                                 │
│    → Deepgram Nova-2  (STT, noise-suppressed)        │
│    → IntentService    (keyword → framework)          │
│    → Groq LLaMA 3.3   (structured prompt gen)        │
│    → MongoDB Atlas    (history saved)                │
└─────────────────────────────────────────────────────┘
```

### Intent → Framework Mapping

| You say… | Intent | Framework |
|----------|--------|-----------|
| "write an email about…" | writing | **CO-STAR** |
| "code a function that…" | coding | **Chain of Thought** |
| "business plan for…" | business | **ROSES** |
| "help me decide between…" | problem_solving | **Tree of Thoughts** |
| anything else | quick | **RFGF** |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- MongoDB Atlas account (free M0 tier)
- Deepgram API key (free tier — 45 min audio/month)
- Groq API key (free tier)

### 1. Clone & setup backend

```bash
git clone <repo-url>
cd prompt_project/backend

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys:
```

```env
GROQ_API_KEY=gsk_...
DEEPGRAM_API_KEY=b27a...
MONGODB_URI=mongodb+srv://user:pass@cluster0.mongodb.net/
MONGODB_DB_NAME=voiceprompt
```

### 3. Start the backend

```bash
# In backend/
uvicorn core.apis.api:app --reload --port 8000
```

Verify at [http://localhost:8000/health](http://localhost:8000/health) and [http://localhost:8000/docs](http://localhost:8000/docs).

### 4. Run the desktop app

```bash
# In a new terminal, from project root
.\backend\venv\Scripts\python.exe desktop\main.py
```

The 🎙️ tray icon appears. Hold `Ctrl+Space` to record!

---

## 📁 Project Structure

```
prompt_project/
├── backend/                  # FastAPI server
│   ├── main.py               # Uvicorn entry point
│   ├── .env                  # API keys (git-ignored)
│   ├── requirements.txt
│   └── core/
│       ├── apis/
│       │   ├── api.py        # FastAPI app + router registration
│       │   └── routers/
│       │       ├── voice.py  # POST /voice/process
│       │       └── history.py# GET/DELETE /history
│       ├── services/
│       │   ├── deepgram_service.py
│       │   ├── intent_service.py
│       │   ├── groq_service.py
│       │   └── history_service.py
│       ├── models/
│       │   └── prompt_model.py
│       └── db/
│           └── mongodb.py
│
└── desktop/                  # PyQt6 tray app
    ├── main.py               # Entry point
    ├── config.py             # ~/.voiceprompt/config.json
    ├── requirements.txt
    ├── build.bat             # PyInstaller build script
    ├── voiceprompt.spec      # PyInstaller spec
    ├── core/
    │   ├── audio_recorder.py # sounddevice → WAV bytes
    │   ├── text_injector.py  # pyperclip + pyautogui
    │   └── api_client.py     # httpx → backend
    └── ui/
        ├── overlay.py        # Animated floating panel
        ├── settings_window.py# Dark settings UI
        └── tray_app.py       # Tray + hotkey + pipeline
```

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/health` | Server status |
| `POST` | `/voice/process` | Upload WAV → structured prompt |
| `GET`  | `/history` | List all saved prompts |
| `GET`  | `/history/{id}` | Get one prompt |
| `DELETE` | `/history/{id}` | Delete one prompt |

### `POST /voice/process`

**Request** (multipart form):
- `file`: WAV or WebM audio file
- `language`: `en` | `hi` | `mr` (default: `en`)

**Response**:
```json
{
  "id": "65f3a...",
  "transcript": "write a blog post about AI",
  "intent": "writing",
  "framework": "CO-STAR",
  "generated_prompt": "## Context\n...\n## Objective\n...",
  "language": "en",
  "processing_time_ms": 1423,
  "created_at": "2026-03-07T10:00:00Z"
}
```

---

## 📦 Build .exe (Windows)

```bash
cd desktop
build.bat
```

Output: `desktop/dist/VoicePromptAI/VoicePromptAI.exe`

> ⚠️ **Important**: Copy your backend `.env` file next to the `.exe` before distributing, **or** configure the backend URL in Settings to point to a deployed server.

---

## ⚙️ Configuration

Settings are persisted at `%USERPROFILE%\.voiceprompt\config.json`.

| Key | Default | Description |
|-----|---------|-------------|
| `api_url` | `http://127.0.0.1:8000` | Backend server URL |
| `language` | `en` | Audio language code |
| `hotkey` | `ctrl+space` | Push-to-talk hotkey |
| `auto_copy` | `true` | Auto-paste into active window |
| `show_transcript` | `true` | Show preview in overlay |
| `sample_rate` | `16000` | Microphone sample rate (Hz) |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop UI | PyQt6 6.6+ |
| Audio capture | sounddevice + numpy |
| Text injection | pyperclip + pyautogui |
| Global hotkey | keyboard |
| Backend | FastAPI + uvicorn |
| STT | Deepgram Nova-2 |
| LLM | Groq LLaMA 3.3-70b |
| Database | MongoDB Atlas |
| HTTP client | httpx |
| Packaging | PyInstaller |

---

## 🔍 Troubleshooting

**Backend offline indicator in tray**
→ Make sure `uvicorn core.apis.api:app --reload --port 8000` is running in the `backend/` directory.

**Hotkey not working**
→ Try running the desktop app as Administrator (some security software blocks global hotkeys).

**Microphone not capturing**
→ Check Windows Privacy Settings → Microphone → allow all apps.

**Empty transcript error**
→ Speak louder/clearer. Minimum ~0.5 seconds of speech.

**MongoDB connection error**
→ Whitelist your IP in MongoDB Atlas → Network Access → Add IP Address → Add Current IP.

---

## 📝 Notes

- Audio is **never written to disk** — processed entirely in memory
- Settings are stored at `~/.voiceprompt/config.json`
- MongoDB only stores transcript + generated prompt text (no audio)
- All API keys are read from `.env` — never hardcoded

---

## 🔮 Future (Phase 6)

- History browser window in the desktop app
- Favourite/star prompts
- Custom framework templates
- Auto-update feature
- Tray icon colour reflects recording state
- Full Hindi & Marathi language support
