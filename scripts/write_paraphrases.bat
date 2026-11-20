@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
echo Step 1: checking which models your keys can use...
python -u code\run_llm_v2.py --probe > logs\model_check_log.txt 2>&1
type logs\model_check_log.txt
echo Step 2: writing the paraphrases...
python -u code\make_paraphrases.py > logs\paraphrase_log.txt 2>&1
type logs\paraphrase_log.txt
echo DONE - you can close this window.
pause
