import pyperclip
import threading
import time

ZIGSY_COMMANDS = {
    "stash this", "stash", "ghost", "ghost mode", "status",
    "vitals", "system status", "explain", "yes", "yes explain"
}

class ClipboardWatcher:
    def __init__(self, on_word, on_phrase):
        """
        on_word   — 1-2 words copied: auto explain as dictionary
        on_phrase — 3-50 words copied: prompt user to type 'explain'
        Ignores anything over 50 words.
        """
        self.on_word   = on_word
        self.on_phrase = on_phrase
        self.running   = False
        self._last     = ""

    def start(self):
        self.running = True
        threading.Thread(target=self._watch, daemon=True).start()

    def stop(self):
        self.running = False

    def _watch(self):
        while self.running:
            try:
                current = pyperclip.paste().strip().rstrip("?!.,;:")
                if current and current != self._last:
                    self._last = current
                    if current.lower() in ZIGSY_COMMANDS:
                        continue  # skip — it's a command not content
                    word_count = len(current.split())
                    if word_count <= 2 and len(current) > 1:
                        self.on_word(current)
                    elif 3 <= word_count <= 50:
                        self.on_phrase(current)
                    # Over 50 words — ignore silently
            except Exception:
                pass
            time.sleep(1)


def get_clipboard() -> str:
    """Get current clipboard text safely."""
    try:
        return pyperclip.paste().strip()
    except Exception:
        return ""