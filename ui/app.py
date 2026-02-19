import customtkinter as ctk
import threading
import sounddevice as sd
import soundfile as sf
import whisper
import numpy as np
import os
import sys
import random

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.tts import speak
from core.llm import chat
from core.rag import load_or_build_index, get_context
from core.memory import load_memory, get_memory_context, add_confusion, add_note
from tools.screen_context import get_active_window_info
from tools.system_tools import find_file, open_folder, is_vague_query, is_natural_language, get_system_vitals, stash_clipboard
from tools.clipboard import ClipboardWatcher, get_clipboard

TASK_KEYWORDS = [
    "how to", "how do i", "help me", "steps to",
    "whatsapp", "wifi", "zoom", "call", "message",
    "settings", "connect", "send", "open", "install",
    "shortcut", "keyboard", "unity", "editor"
]
SCREEN_KEYWORDS = [
    "which screen", "what screen", "where am i", "which app",
    "what is open", "what am i looking at", "what is this",
    "i am confused", "i'm confused", "lost", "what do i see"
]
CONFUSION_KEYWORDS = ["whatsapp", "wifi", "zoom", "camera", "shortcut", "unity"]
FIND_TRIGGERS = ["find me", "search for", "locate", "find"]
FILLER_WORDS = {"my", "the", "a", "an", "this", "that", "some", "any", "of", "mine"}

QUICK_ACTIONS = [
    ("📱 WhatsApp Call",  "How do I make a video call on WhatsApp?"),
    ("🌐 Connect WiFi",   "How do I connect to WiFi?"),
    ("🔠 Bigger Text",    "How do I make the text bigger on my screen?"),
    ("🔄 Restart PC",     "How do I restart my computer?"),
    ("📹 Zoom Meeting",   "How do I join a Zoom meeting?"),
    ("📁 Find a File",    "How do I find a file on my computer?"),
]


def needs_rag(text):
    return any(k in text.lower() for k in TASK_KEYWORDS)


def needs_screen_context(text):
    return any(k in text.lower() for k in SCREEN_KEYWORDS)


def extract_filename(user_input):
    text = user_input.lower().strip().rstrip("?!.")
    user_input = user_input.rstrip("?!.")
    if is_vague_query(text) or is_natural_language(text):
        return None
    for trigger in FIND_TRIGGERS:
        if text.startswith(trigger):
            result = user_input[len(trigger):].strip()
            words = result.split()
            while words and words[0].lower() in FILLER_WORDS:
                words.pop(0)
            return " ".join(words)
    return None


class ZigsyApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ZIGSY // COMMAND BRIDGE")
        self.geometry("1000x900")
        self.minsize(800, 700)

        self.color_space_bg    = "#0B0E14"
        self.color_panel_bg    = "#161B22"
        self.color_orange_neon = "#FF8C00"
        self.color_grid        = "#1B222A"
        self.color_text        = "#E6E6E6"

        self.configure(fg_color=self.color_space_bg)
        ctk.set_appearance_mode("dark")

        self.history       = []
        self.memory        = load_memory()
        self.whisper_model = None
        self.recording     = False
        self.audio_data    = []
        self.index         = None
        self.open_btn      = None
        self.font_size     = 15
        self.ghost_mode    = False

        self.setup_ui()

        self.clipboard_watcher = ClipboardWatcher(
            on_word=self.on_clipboard_word,
            on_phrase=self.on_clipboard_phrase
        )
        self.clipboard_watcher.start()

        threading.Thread(target=self.load_backend, daemon=True).start()

    def setup_ui(self):
        self.bg_canvas = ctk.CTkCanvas(self, bg=self.color_space_bg, highlightthickness=0)
        self.bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.draw_tactical_elements()

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header_label = ctk.CTkLabel(
            self,
            text="[ ZIGSY // COMMAND BRIDGE  •  STATUS: OFFLINE ]",
            font=("Consolas", 12, "bold"),
            text_color=self.color_orange_neon
        )
        self.header_label.grid(row=0, column=0, padx=40, pady=(15, 0), sticky="w")

        outer = ctk.CTkFrame(self, fg_color=self.color_orange_neon, corner_radius=10)
        outer.grid(row=1, column=0, padx=40, pady=(10, 5), sticky="nsew")
        inner = ctk.CTkFrame(outer, fg_color=self.color_panel_bg, corner_radius=8)
        inner.pack(padx=2, pady=2, fill="both", expand=True)

        self.chat_box = ctk.CTkTextbox(
            inner,
            font=("Consolas", self.font_size),
            fg_color="transparent",
            text_color=self.color_text,
            wrap="word",
            state="disabled"
        )
        self.chat_box.pack(padx=20, pady=15, fill="both", expand=True)

        qa_frame = ctk.CTkFrame(self, fg_color="transparent")
        qa_frame.grid(row=2, column=0, padx=40, pady=(5, 5), sticky="ew")
        for i, (label, message) in enumerate(QUICK_ACTIONS):
            btn = ctk.CTkButton(
                qa_frame,
                text=label,
                font=("Consolas", 12),
                height=36,
                fg_color=self.color_panel_bg,
                border_color=self.color_orange_neon,
                border_width=1,
                text_color=self.color_orange_neon,
                hover_color="#331C00",
                corner_radius=5,
                command=lambda m=message: self.send_message(m)
            )
            btn.grid(row=0, column=i, padx=4, sticky="ew")
            qa_frame.grid_columnconfigure(i, weight=1)

        input_frame = ctk.CTkFrame(self, fg_color="transparent")
        input_frame.grid(row=3, column=0, padx=40, pady=(5, 30), sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        self.input_field = ctk.CTkEntry(
            input_frame,
            placeholder_text="> QUERY DATASTREAM...",
            font=("Consolas", 15),
            height=55,
            fg_color=self.color_panel_bg,
            border_color=self.color_orange_neon,
            text_color=self.color_text,
            corner_radius=5,
            state="disabled"
        )
        self.input_field.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        self.input_field.bind("<Return>", lambda e: self.send_message())

        self.mic_btn = ctk.CTkButton(
            input_frame, text="VOX",
            fg_color="transparent", text_color=self.color_orange_neon,
            border_color=self.color_orange_neon, border_width=2,
            width=80, height=55, corner_radius=5,
            hover_color="#331C00", state="disabled",
            command=self.toggle_recording
        )
        self.mic_btn.grid(row=0, column=1, padx=5)

        self.send_btn = ctk.CTkButton(
            input_frame, text="EXEC",
            fg_color=self.color_orange_neon, text_color=self.color_space_bg,
            font=("Consolas", 16, "bold"),
            width=100, height=55, corner_radius=5,
            hover_color="#FFA500", state="disabled",
            command=self.send_message
        )
        self.send_btn.grid(row=0, column=2, padx=5)

    def draw_tactical_elements(self):
        for i in range(0, 1200, 40):
            self.bg_canvas.create_line(i, 0, i, 1000, fill=self.color_grid)
        for i in range(0, 1000, 40):
            self.bg_canvas.create_line(0, i, 1200, i, fill=self.color_grid)
        for _ in range(80):
            x, y = random.randint(0, 1200), random.randint(0, 1000)
            s = random.choice([1, 2])
            self.bg_canvas.create_rectangle(x, y, x+s, y+s, fill="#4B5563", outline="")

    def append_chat(self, sender, message):
        def _append():
            self.chat_box.configure(state="normal")
            prefix = "// USER >  " if sender == "You" else "// ZIGSY > "
            self.chat_box.insert("end", prefix + f"{message}\n\n")
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")
        self.after(0, _append)

    def set_status(self, text):
        self.after(0, lambda: self.header_label.configure(
            text=f"[ ZIGSY // COMMAND BRIDGE  •  {text} ]"
        ))

    def enable_input(self):
        self.after(0, lambda: self.input_field.configure(state="normal"))
        self.after(0, lambda: self.send_btn.configure(state="normal"))

    def disable_input(self):
        self.input_field.configure(state="disabled")
        self.send_btn.configure(state="disabled")

    def show_open_button(self, folder_path):
        def _show():
            if self.open_btn and self.open_btn.winfo_exists():
                self.open_btn.destroy()
            self.open_btn = ctk.CTkButton(
                self,
                text=f"📁 Open Folder: {os.path.basename(folder_path)}",
                font=("Consolas", 12),
                height=32,
                fg_color=self.color_panel_bg,
                border_color=self.color_orange_neon,
                border_width=1,
                text_color=self.color_orange_neon,
                hover_color="#331C00",
                corner_radius=5,
                command=lambda p=folder_path: [open_folder(p), self.open_btn.destroy()]
            )
            self.open_btn.grid(row=2, column=0, padx=40, pady=(2, 2), sticky="ew")
        self.after(0, _show)

    # ── Clipboard handlers ────────────────────────────────────────────────────

    def on_clipboard_word(self, text):
        prompt = f"Define this word or term in simple, clear language in 2-3 sentences maximum: '{text}'"
        self.append_chat("Zigsy", f"📖 Defining: \"{text}\"")
        threading.Thread(target=self._clipboard_response, args=(prompt,), daemon=True).start()

    def on_clipboard_phrase(self, text):
        self._pending_clipboard = text
        preview = text[:80] + "..." if len(text) > 80 else text
        self.append_chat("Zigsy", f"📋 Copied: \"{preview}\"\nType 'explain' if you want me to explain this.")

    def _clipboard_response(self, prompt):
        response = chat(prompt, [], context="")
        self.append_chat("Zigsy", response)
        speak(response)

    # ── Backend ───────────────────────────────────────────────────────────────

    def load_backend(self):
        self.set_status("SYNCING...")
        self.append_chat("Zigsy", "SYNCING TACTICAL DATA...")
        self.index = load_or_build_index()
        self.enable_input()
        self.after(0, lambda: self.mic_btn.configure(state="normal"))
        self.set_status("STATUS: NOMINAL")
        self.append_chat("Zigsy", "SYSTEM READY. How can I help you today?")

    def send_message(self, text=None):
        user_input = text or self.input_field.get().strip()
        if not user_input:
            return
        self.input_field.delete(0, "end")
        self.append_chat("You", user_input)

        lower = user_input.lower().strip()

        # ── Special commands (no LLM needed) ─────────────────────────────
        if lower.startswith("remember that"):
            note = user_input[len("remember that"):].strip()
            add_note(self.memory, note)
            self.append_chat("Zigsy", "Got it, I'll remember that!")
            return

        if lower in ["ghost", "ghost mode"]:
            self.ghost_mode = not self.ghost_mode
            alpha = 0.5 if self.ghost_mode else 1.0
            self.attributes("-alpha", alpha)
            state = "ON — I'm semi-transparent now." if self.ghost_mode else "OFF — Back to full opacity."
            self.append_chat("Zigsy", f"👻 Ghost Mode {state}")
            return

        if lower in ["status", "vitals", "system status"]:
            result = get_system_vitals()
            self.append_chat("Zigsy", result)
            return

        if lower in ["stash", "stash this"]:
            clipboard_text = get_clipboard()
            if clipboard_text:
                result = stash_clipboard(clipboard_text)
                self.append_chat("Zigsy", result)
            else:
                self.append_chat("Zigsy", "Nothing in clipboard to stash.")
            return

        if lower in ["explain", "yes explain", "yes"]:
            clipboard_text = get_clipboard()
            if clipboard_text:
                user_input = f"Explain this in simple terms: {clipboard_text}"
            else:
                self.append_chat("Zigsy", "Nothing in clipboard to explain.")
                return

        self.disable_input()
        threading.Thread(target=self.get_response, args=(user_input,), daemon=True).start()

    def get_response(self, user_input):
        self.set_status("PROCESSING...")

        # File search
        filename = extract_filename(user_input)
        if filename:
            result = find_file(filename)
            if result is not None:
                result_text, folder_path = result
                self.after(0, lambda: self.append_chat("Zigsy", result_text))
                if folder_path:
                    self.show_open_button(folder_path)
                self.enable_input()
                self.set_status("STATUS: NOMINAL")
                return

        # Build LLM context
        context_parts = []

        memory_context = get_memory_context(self.memory)
        if memory_context:
            context_parts.append(memory_context)

        if needs_screen_context(user_input):
            screen_info = get_active_window_info()
            if screen_info:
                context_parts.append(screen_info)

        if needs_rag(user_input) and self.index:
            rag_context = get_context(user_input, self.index)
            if rag_context:
                context_parts.append(rag_context)
            for keyword in CONFUSION_KEYWORDS:
                if keyword in user_input.lower():
                    add_confusion(self.memory, keyword)

        context = "\n\n".join(context_parts)

        self.append_chat("Zigsy", "Thinking...")
        response = chat(user_input, self.history, context=context)

        def _update():
            self.chat_box.configure(state="normal")
            content = self.chat_box.get("1.0", "end")
            content = content.replace("// ZIGSY > Thinking...\n\n", "")
            self.chat_box.delete("1.0", "end")
            self.chat_box.insert("1.0", content)
            self.chat_box.configure(state="disabled")
            self.append_chat("Zigsy", response)
            speak(response)
            self.enable_input()
            self.set_status("STATUS: NOMINAL")

        self.after(0, _update)
        self.history.append({"role": "user", "content": user_input})
        self.history.append({"role": "assistant", "content": response})

    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.audio_data = []
            self.mic_btn.configure(text="REC", fg_color="#7F1D1D", text_color="white")
            threading.Thread(target=self.record_audio, daemon=True).start()
        else:
            self.recording = False
            self.mic_btn.configure(text="VOX", fg_color="transparent", text_color=self.color_orange_neon)
            threading.Thread(target=self.transcribe_audio, daemon=True).start()

    def record_audio(self):
        with sd.InputStream(samplerate=16000, channels=1, dtype="float32") as stream:
            while self.recording:
                chunk, _ = stream.read(1024)
                self.audio_data.append(chunk)

    def transcribe_audio(self):
        if not self.audio_data:
            return
        if self.whisper_model is None:
            self.append_chat("Zigsy", "Loading voice model for first time...")
            self.whisper_model = whisper.load_model("tiny")
        self.append_chat("Zigsy", "Transcribing...")
        audio = np.concatenate(self.audio_data, axis=0).flatten()
        sf.write("temp_audio.wav", audio, 16000)
        result = self.whisper_model.transcribe("temp_audio.wav")
        text = result["text"].strip()
        os.remove("temp_audio.wav")
        if text:
            self.after(0, lambda: self.send_message(text))


if __name__ == "__main__":
    app = ZigsyApp()
    app.mainloop()