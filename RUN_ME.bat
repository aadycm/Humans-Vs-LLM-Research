@echo off
cd /d "%~dp0"
echo ENVSE 497 LLM run (gpt-4o-mini, gpt-4.1, gpt-4o). Do not close this window.
python run_llm.py > data_full_log.txt 2>&1
type data_full_log.txt
echo.
echo ALL DONE - you can close this window.
pause
