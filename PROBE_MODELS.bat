@echo off
cd /d "%~dp0"
python -u run_llm_v2.py --probe > data_probe_log.txt 2>&1
type data_probe_log.txt
echo DONE - you can close this window.
pause
