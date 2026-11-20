@echo off
cd /d "%~dp0.."
if not exist logs mkdir logs
echo Pushing latest changes to GitHub ...
set MSG=Update project files
set /p MSG=Short note about what changed (press Enter to skip): 
git add -A
git commit -m "%MSG%"
git push > logs\push_log.txt 2>&1
type logs\push_log.txt
echo.
echo DONE - you can close this window.
pause
