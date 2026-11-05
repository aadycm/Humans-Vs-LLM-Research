@echo off
cd /d "%~dp0"
echo Pushing latest changes to GitHub ...
git add -A
git commit -m "Update project files"
git push > push_log.txt 2>&1
type push_log.txt
echo.
echo DONE - you can close this window.
pause
