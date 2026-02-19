# import json
# import os

# MEMORY_FILE = "memory.json"

# def load_memory() -> dict:
#     if os.path.exists(MEMORY_FILE):
#         with open(MEMORY_FILE, "r") as f:
#             return json.load(f)
#     return {"confusion_points": [], "user_name": None, "user_notes": []}

# def save_memory(memory: dict):
#     with open(MEMORY_FILE, "w") as f:
#         json.dump(memory, f, indent=2)

# def add_confusion(memory: dict, topic: str):
#     if topic not in memory["confusion_points"]:
#         memory["confusion_points"].append(topic)
#         save_memory(memory)

# def add_note(memory: dict, note: str):
#     if note not in memory["user_notes"]:
#         memory["user_notes"].append(note)
#         save_memory(memory)

# def get_memory_context(memory: dict) -> str:
#     parts = []
#     if memory["confusion_points"]:
#         topics = ", ".join(memory["confusion_points"])
#         parts.append(f"This user has previously struggled with: {topics}. Be extra patient about these.")
#     if memory.get("user_notes"):
#         notes = "; ".join(memory["user_notes"])
#         parts.append(f"Important things to remember about this user: {notes}")
#     return "\n".join(parts)

import json
import os

MEMORY_FILE = "memory.json"

def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"confusion_points": [], "user_name": None, "user_notes": []}

def save_memory(memory: dict):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def add_confusion(memory: dict, topic: str):
    if topic not in memory["confusion_points"]:
        memory["confusion_points"].append(topic)
        save_memory(memory)

def add_note(memory: dict, note: str):
    if note not in memory["user_notes"]:
        memory["user_notes"].append(note)
        save_memory(memory)

def get_memory_context(memory: dict) -> str:
    parts = []

    if memory.get("confusion_points"):
        topics = ", ".join(memory["confusion_points"])
        parts.append(f"Topics this user has struggled with: {topics}. Be extra patient about these.")

    if memory.get("user_notes"):
        notes_formatted = "\n".join(
            f"  - {note}" for note in memory["user_notes"]
        )
        parts.append(
            f"IMPORTANT FACTS about this user — treat each one as separate and distinct:\n{notes_formatted}"
        )

    return "\n\n".join(parts)