import os
import re
import subprocess
import psutil
import datetime

# ── Directories to always skip ─────────────────────────────────────────────
SKIP_DIRS = {
    'Windows', 'Program Files', 'Program Files (x86)',
    'node_modules', 'site-packages', '__pycache__',
    '.git', 'venv', 'myenv', '$Recycle.Bin',
    'WinSxS', 'System32', 'SysWOW64', 'AppData',
    'Temp', 'tmp', '.vs', 'obj', 'bin', 'build',
    'dist', '.next', '.nuxt', 'coverage'
}

FILLER_WORDS = {
    "my", "the", "a", "an", "this", "that", "some", "any",
    "of", "mine", "please", "can", "you"
}

NATURAL_LANGUAGE_PATTERNS = [
    r"where is .+ installed",
    r"where (is|are) .+ (located|saved|stored|kept)",
    r"how (do|can) i find",
    r"what (is|are) .+ (file|folder)",
]

VAGUE_PATTERNS = [
    r"something about",
    r"related to",
    r"that pdf",
    r"that file",
    r"the one with",
    r"i think it was",
    r"not sure",
    r"similar to",
    r"something like",
]


def is_natural_language(query: str) -> bool:
    q = query.lower()
    for pattern in NATURAL_LANGUAGE_PATTERNS:
        if re.search(pattern, q):
            return True
    words = q.split()
    has_extension = any("." in w for w in words)
    if len(words) > 5 and not has_extension:
        return True
    return False


def is_vague_query(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in VAGUE_PATTERNS)


def clean_search_term(raw: str) -> str:
    raw = re.sub(
        r"[?!.]+$", "", raw
    ).strip()
    raw = re.sub(
        r"\s+(or something.*|on (desktop|computer|laptop|pc|my computer)|file|folder|document|of mine|please)$",
        "", raw, flags=re.IGNORECASE
    ).strip()
    words = raw.split()
    while words and words[0].lower() in FILLER_WORDS:
        words.pop(0)
    return " ".join(words).strip()


def get_search_paths():
    home = os.path.expanduser("~")
    cwd = os.getcwd()
    paths = [
        cwd,
        os.path.join(home, "Desktop"),
        os.path.join(home, "Documents"),
        os.path.join(home, "Downloads"),
        os.path.join(home, "Pictures"),
        os.path.join(home, "Videos"),
        os.path.join(home, "Music"),
        home,
        "C:\\",
    ]
    seen = set()
    return [p for p in paths if p not in seen and not seen.add(p) and os.path.exists(p)]


def matches(name: str, term: str) -> bool:
    n = name.lower()
    t = term.lower()
    if t.startswith('.'):
        return n.endswith(t)
    return (
        n == t or
        n.startswith(t) or
        bool(re.search(r'\b' + re.escape(t) + r'\b', n))
    )


def format_result(icon: str, path: str) -> str:
    name = os.path.basename(path)
    is_dir = os.path.isdir(path)
    label = "FOLDER" if is_dir else "FILE"
    line = f"{icon} {name} [{label}]\n📍 {path}\n"
    if not is_dir:
        try:
            size = os.path.getsize(path)
            line += f"📦 {size // 1024} KB\n" if size > 1024 else f"📦 {size} B\n"
        except Exception:
            pass
    return line + "\n"


def find_file(raw_query: str):
    if is_natural_language(raw_query) or is_vague_query(raw_query):
        return None

    search_term = clean_search_term(raw_query)
    if not search_term:
        return ("Please tell me the filename you're looking for.", None)

    found = []
    found_paths = set()

    for base_path in get_search_paths():
        for root, dirs, files in os.walk(base_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]
            for d in dirs:
                if matches(d, search_term):
                    full = os.path.normpath(os.path.join(root, d))
                    if full not in found_paths:
                        found.append(("📁", full))
                        found_paths.add(full)
            for f in files:
                if matches(f, search_term):
                    full = os.path.normpath(os.path.join(root, f))
                    if full not in found_paths:
                        found.append(("📄", full))
                        found_paths.add(full)
            if len(found) >= 15:
                break
        if len(found) >= 15:
            break

    if not found:
        return (f"Could not find '{search_term}'. Check the spelling or try a shorter name.", None)

    output = f"Found {len(found)} match(es) for '{search_term}':\n\n"
    for icon, path in found[:5]:
        output += format_result(icon, path)
    if len(found) > 5:
        output += f"...and {len(found) - 5} more. Be more specific to narrow results.\n"

    first_folder = None
    for icon, path in found[:1]:
        first_folder = path if os.path.isdir(path) else os.path.dirname(path)

    return (output.strip(), first_folder)


def open_folder(path: str) -> str:
    path = path.strip().strip('"').strip("'")
    if os.path.isfile(path):
        path = os.path.dirname(path)
    if not os.path.exists(path):
        return f"Could not find '{path}'."
    try:
        subprocess.Popen(f'explorer "{path}"')
        return f"Opened File Explorer at:\n📁 {path}"
    except Exception as e:
        return f"Could not open folder: {e}"


def get_system_vitals() -> str:
    """Returns CPU, RAM and battery stats."""
    try:
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_used = ram.used // (1024 ** 2)
        ram_total = ram.total // (1024 ** 2)
        ram_free = ram.available // (1024 ** 2)

        battery = psutil.sensors_battery()
        if battery:
            bat_pct = battery.percent
            charging = "⚡ Charging" if battery.power_plugged else "🔋 On Battery"
            bat_line = f"Battery:  {bat_pct:.0f}%  {charging}"
        else:
            bat_line = "Battery:  Not available"

        return (
            f"── SYSTEM VITALS ──────────────────\n"
            f"CPU:      {cpu:.1f}% used\n"
            f"RAM:      {ram_used} MB used / {ram_total} MB total ({ram_free} MB free)\n"
            f"{bat_line}\n"
            f"───────────────────────────────────"
        )
    except Exception as e:
        return f"Could not read system vitals: {e}"


def stash_clipboard(text: str) -> str:
    """Appends clipboard text to stash.md with timestamp."""
    stash_path = os.path.join(os.getcwd(), "stash.md")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n---\n**{timestamp}**\n\n{text}\n"
    try:
        with open(stash_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return f"Stashed to stash.md ✅\n📍 {stash_path}"
    except Exception as e:
        return f"Could not stash: {e}"