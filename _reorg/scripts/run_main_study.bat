@echo off
cd /d "%~dp0.."
echo ENVSE 497 main study run (gpt-4o-mini, gpt-4.1, gpt-4o). Do not close this window.
python -u code\run_llm.py > logs\main_study_run_log.txt 2>&1
type logs\main_study_run_log.txt
echo.
echo ALL DONE - you can close this window.
pause
