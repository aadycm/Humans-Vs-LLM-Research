@echo off
cd /d "%~dp0"
echo ENVSE 497 follow-up: FULL run. This takes about 1 to 3 hours.
echo Keep this window open and the laptop awake and plugged in.
echo If it stops for any reason, double-click this file again: finished runs are kept.
python -u run_llm_v2.py --log data_v2_full_log.txt
echo.
echo FINISHED. Tell Claude the full run is done.
pause
