@echo off
REM
call venv\Scripts\activate

REM
pip install -r requirements.txt

REM \
"%~dp0venv\Scripts\python.exe" -u -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
