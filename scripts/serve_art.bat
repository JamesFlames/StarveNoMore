@echo off
echo Starting art asset server at http://localhost:8080
echo TTS will load images from this server during local development.
echo Keep this window open while playing in TTS.
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0..\art"
python -m http.server 8080
