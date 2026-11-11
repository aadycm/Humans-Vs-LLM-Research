@echo off
cd /d "%~dp0"
echo Step 1: checking which models your keys can use...
python -u run_llm_v2.py --probe > data_probe_log.txt 2>&1
type data_probe_log.txt
echo Step 2: writing paraphrases with Claude...
python -u make_paraphrases.py > data_paraphrase_log.txt 2>&1
type data_paraphrase_log.txt
echo DONE - you can close this window.
pause
