@echo off
cd /d "%~dp0"
C:\Users\VIVEK\AppData\Local\Programs\Python\Python310\pythonw.exe main.py
if %errorlevel% neq 0 (
    echo Something went wrong. Press any key to see the error.
    pause
)