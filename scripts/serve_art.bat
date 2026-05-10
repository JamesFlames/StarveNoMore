@echo off
echo Starting StarveNoMore asset server at http://localhost:8080
echo Serves the repo root so both art\ and sounds\ are reachable, e.g.:
echo   http://localhost:8080/art/board/main_board.png
echo   http://localhost:8080/sounds/ambient/suburban/...wav
echo Keep this window open while playing in TTS.
echo Press Ctrl+C to stop.
echo.
cd /d "%~dp0.."
python -m http.server 8080
