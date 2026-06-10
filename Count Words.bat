@echo off
python "%~dp0count_words.py"
if %errorlevel% neq 0 (
    echo.
    echo Something went wrong. Make sure Python is installed.
    echo Download it from https://www.python.org/downloads/
    pause
)
