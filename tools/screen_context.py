import subprocess
import threading
import time

# Stores the last known non-Zigsy window
_last_known_window = ""
_lock = threading.Lock()

KNOWN_APPS = {
    "chrome": "Google Chrome",
    "msedge": "Microsoft Edge",
    "firefox": "Firefox",
    "whatsapp": "WhatsApp",
    "zoom": "Zoom",
    "notepad": "Notepad",
    "winword": "Microsoft Word",
    "excel": "Microsoft Excel",
    "powerpnt": "Microsoft PowerPoint",
    "code": "Visual Studio Code",
    "powershell": "PowerShell",
    "cmd": "Command Prompt",
    "mspaint": "Paint",
    "vlc": "VLC Media Player",
    "explorer": "File Explorer",
    "systemsettings": "Windows Settings",
    "control": "Control Panel",
    "mmc": "Computer Management",
    "taskmgr": "Task Manager",
    "regedit": "Registry Editor",
    "msconfig": "System Configuration",
    "shellexperiencehost": "the Desktop",
}

SKIP_TITLE_APPS = {"code", "powershell", "cmd", "regedit", "mmc", "msconfig"}
IGNORE_PROCESSES = {"zigsy", "python", "python3", "py"}


def _format_window(title: str, process: str) -> str:
    if not title or title.isdigit() or len(title) < 3:
        return ""
    app_name = KNOWN_APPS.get(process, process.capitalize())
    if process in SKIP_TITLE_APPS:
        return f"The user has {app_name} open on their screen"
    if title:
        return f"The user has {app_name} open, showing: {title}"
    return f"The user has {app_name} open on their screen"


def _poll_active_window():
    global _last_known_window
    script = """
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class WinAPI {
    [DllImport("user32.dll")]
    public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")]
    public static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);
    [DllImport("user32.dll")]
    public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
}
"@
$hwnd = [WinAPI]::GetForegroundWindow()
$title = New-Object System.Text.StringBuilder 256
[WinAPI]::GetWindowText($hwnd, $title, 256)
$pid = 0
[WinAPI]::GetWindowThreadProcessId($hwnd, [ref]$pid)
$process = Get-Process -Id $pid
Write-Output "$($title.ToString())|$($process.Name)"
"""
    while True:
        try:
            result = subprocess.run(
                ["powershell", "-Command", script],
                capture_output=True, text=True, timeout=3
            )
            output = result.stdout.strip()
            if "|" in output:
                title, process = output.split("|", 1)
                title = title.strip()
                process = process.strip().lower()
                if any(ig in process for ig in IGNORE_PROCESSES):
                    time.sleep(2)
                    continue
                if "zigsy" in title.lower():
                    time.sleep(2)
                    continue
                info = _format_window(title, process)
                if info:
                    with _lock:
                        _last_known_window = info
        except Exception:
            pass
        time.sleep(2)


def get_active_window_info() -> str:
    with _lock:
        return _last_known_window


# Start background monitor automatically when module is imported
_monitor = threading.Thread(target=_poll_active_window, daemon=True)
_monitor.start()