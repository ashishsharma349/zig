import threading
import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import os

VOSK_MODEL_PATH = "vosk-model-small-en-us-0.15/vosk-model-small-en-us-0.15"

class WakeWordListener:
    def __init__(self, wake_word="hey zigsy", on_detected=None):
        self.wake_word = wake_word.lower()
        self.on_detected = on_detected
        self.running = False
        self.audio_queue = queue.Queue()
        self.model = None
        self.recognizer = None

        if not os.path.exists(VOSK_MODEL_PATH):
            print(f"[Wake Word] Vosk model not found at {VOSK_MODEL_PATH}")
            return

        try:
            self.model = Model(VOSK_MODEL_PATH)
            self.recognizer = KaldiRecognizer(self.model, 16000)
            print("[Wake Word] Model loaded successfully")
        except Exception as e:
            print(f"[Wake Word] Failed to load model: {e}")

    def start(self):
        if self.recognizer is None:
            print("[Wake Word] Cannot start — model not loaded")
            return
        self.running = True
        threading.Thread(target=self._listen_loop, daemon=True).start()
        print("[Wake Word] Listening for 'hey zigsy'...")

    def stop(self):
        self.running = False

    def _audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(bytes(indata))

    def _listen_loop(self):
        with sd.RawInputStream(samplerate=16000, blocksize=8000,
                               dtype='int16', channels=1,
                               callback=self._audio_callback):
            while self.running:
                try:
                    data = self.audio_queue.get(timeout=1)
                    if self.recognizer.AcceptWaveform(data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").lower()
                        print(f"[Wake Word] Heard: {text}")
                        if self.wake_word in text:
                            if self.on_detected:
                                self.on_detected()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"[Wake Word] Error: {e}")
                    continue