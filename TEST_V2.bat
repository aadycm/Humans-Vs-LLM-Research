@echo off
cd /d "%~dp0"
echo ENVSE 497 follow-up: TEST run (1 run per cell, about 5 minutes).
echo Keep this window open until it says FINISHED.
python -u run_llm_v2.py --test --log data_v2_test_log.txt
echo.
echo FINISHED. Tell Claude the test is done.
pause
