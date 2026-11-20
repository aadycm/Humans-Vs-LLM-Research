@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
python -u code\run_llm_v2.py --probe > logs\model_check_log.txt 2>&1
type logs\model_check_log.txt
echo DONE - you can close this window.
pause
