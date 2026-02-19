# Zigsy — Offline AI Assistant for Windows

A local, private AI assistant that runs entirely on your machine. No internet required for core features. Built for anyone who isn't comfortable with computers — elders, non-tech users, or anyone who wants a simple way to get help with their PC.

---

## What Zigsy Can Do

### 🤖 Talk to It
Ask anything in plain language. Zigsy answers using a local AI model running via Ollama — no data leaves your computer.

### 📁 Find Files
Type `find krishna` or `find resume` and Zigsy searches your entire computer and shows you exactly where the file is with a button to open its folder.

### 📖 Dictionary Mode
Copy any word while reading a PDF or document — Zigsy automatically defines it for you. Copy a sentence and type `explain` to get a simple explanation.

### 💾 System Vitals
Type `status` to instantly see your CPU usage, RAM, and battery percentage.

### 👻 Ghost Mode
Type `ghost` to make Zigsy semi-transparent so you can read what's behind it.

### 📋 Clipboard Stash
Type `stash this` to save whatever you've copied to a `stash.md` file with a timestamp.

### 🎙️ Voice Input
Press VOX, speak, and Zigsy transcribes and responds. All offline.

### 🧠 Memory
Zigsy remembers your name, things you've told it, and topics you've struggled with across sessions.

### 📚 Knowledge Base
Add your own PDF guides and text files to `knowledge_base/raw/` and Zigsy will use them to answer questions accurately.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Ollama (Gemma2:2b / Tenali) |
| RAG | LlamaIndex + BAAI embeddings |
| UI | CustomTkinter |
| Voice Input | OpenAI Whisper (local) |
| TTS | pyttsx3 |
| File Search | os.walk with smart filtering |
| Clipboard | pyperclip |
| System Stats | psutil |
| Memory | JSON persistence |

---

## Project Structure

```
Zigsy/
├── core/
│   ├── llm.py              # Ollama chat with context injection
│   ├── rag.py              # LlamaIndex vector search
│   ├── memory.py           # JSON memory persistence
│   ├── tts.py              # Text to speech
│   └── wake_word.py        # Vosk wake word (optional)
├── knowledge_base/
│   ├── raw/                # Add your .txt and .pdf guides here
│   └── index/              # Auto-generated vector index
├── tools/
│   ├── system_tools.py     # File search, vitals, stash
│   ├── clipboard.py        # Clipboard watcher
│   └── screen_context.py   # Active window detection
├── ui/
│   └── app.py              # Main CustomTkinter UI
├── memory.json             # Persistent user memory
├── stash.md                # Clipboard stash file
└── config.py               # Model name and system prompt
```

---

## Setup

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) and pull a model:
```powershell
ollama pull gemma2:2b
```

### 2. Install Python Dependencies
```powershell
py -m pip install ollama
py -m pip install llama-index llama-index-llms-ollama llama-index-embeddings-huggingface
py -m pip install pymupdf
py -m pip install customtkinter
py -m pip install openai-whisper sounddevice soundfile
py -m pip install pyttsx3
py -m pip install pyperclip
py -m pip install psutil
py -m pip install vosk
```

### 3. Install ffmpeg (required for Whisper)
Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add `bin` folder to your system PATH.

### 4. Run
```powershell
py ui/app.py
```

---

## Commands

| Command | What It Does |
|---------|-------------|
| `find <name>` | Search for a file or folder |
| `explain` | Explain current clipboard content |
| `status` | Show CPU, RAM, battery |
| `ghost` | Toggle window transparency |
| `stash this` | Save clipboard to stash.md |
| `remember that <fact>` | Save a note to memory |

---

## Hardware Tested On

- Intel i3-1215U
- 8GB RAM
- Windows 11

Recommended: Close heavy apps like Chrome before running to free RAM for the model.

---

## Built By

Ashish Sharma — [github.com/ashishsharma349](https://github.com/ashishsharma349)