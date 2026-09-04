@echo off
echo Starting EduClassify Backend...
cd /d "%~dp0"
echo Current directory: %CD%
set TMP=%CD%\tmp
set TEMP=%CD%\tmp
set HF_HOME=%CD%\.cache\huggingface
set TORCH_HOME=%CD%\.cache\torch
set YOLO_CONFIG_DIR=%CD%\.cache\ultralytics
set XDG_CACHE_HOME=%CD%\.cache
set PYTHONUTF8=1
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000 --timeout-keep-alive 300 --h11-max-incomplete-event-size 5242880 --reload-exclude "backend/uploads"

