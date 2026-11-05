@echo off
cd /d "%~dp0"
echo Creating private GitHub repo aadycm/envse497-framing-llm-study ...
if not exist .git git init -b main
git add -A
git status --short
git commit -m "ENVSE 497 framing study: materials, LLM runner and data, analysis, results"
gh repo create aadycm/envse497-framing-llm-study --private --source . --push > repo_log.txt 2>&1
type repo_log.txt
echo.
echo DONE - you can close this window.
pause
