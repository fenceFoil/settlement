rem call ../venv/scripts/Activate.bat
uvicorn app:app --no-access-log --log-level warning --port 80 --host 0.0.0.0