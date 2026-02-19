# import pyttsx3
# import threading

# _engine = None
# _lock = threading.Lock()

# def _get_engine():
#     global _engine
#     if _engine is None:
#         _engine = pyttsx3.init()
#         _engine.setProperty("rate", 150)  # Speed — 150 is calm and clear
#         _engine.setProperty("volume", 1.0)
#     return _engine

# def speak(text: str):
#     """Speak text in a background thread so UI doesn't freeze."""
#     def _speak():
#         with _lock:
#             engine = _get_engine()
#             engine.say(text)
#             engine.runAndWait()
#     threading.Thread(target=_speak, daemon=True).start()

import pyttsx3
import threading

def speak(text: str):
    def _speak():
        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 150)
            engine.setProperty("volume", 1.0)
            engine.say(text)
            engine.runAndWait()
            engine.stop()
        except Exception as e:
            print(f"TTS error: {e}")
    threading.Thread(target=_speak, daemon=True).start()