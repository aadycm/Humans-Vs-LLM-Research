@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
echo ENVSE 497 follow-up: FULL run. This takes about 1 to 3 hours.
echo Keep this window open and the laptop awake and plugged in.
echo If it stops for any reason, run this file again: finished runs are kept.
python -u code\run_llm_v2.py --log logs\followup_run_log.txt
echo.
echo FINISHED.
pause
