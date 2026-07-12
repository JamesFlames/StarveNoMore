@echo off
rem iwanttoplay — rebuild, test, install and launch Starve No More.
rem Usage: iwanttoplay [--skip-tests] [--no-launch]
python "%~dp0scripts\iwanttoplay.py" %*
