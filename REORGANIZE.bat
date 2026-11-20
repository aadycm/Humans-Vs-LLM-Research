@echo off
cd /d "%~dp0"
echo Tidying the repo into folders. This only moves files, nothing is lost.
python reorganize.py
if errorlevel 1 goto fail
del reorganize.py
git add -A
git commit -q -m "Tidy the repo into folders and rewrite the README"
echo.
echo Done. Check the list above, then press a key to push to GitHub (or close this window to stop here).
pause
git push > logs\push_log.txt 2>&1
type logs\push_log.txt
echo.
echo ALL DONE. From now on use scripts\update_repo.bat to push changes.
pause
(goto) 2>nul & del "%~f0"
:fail
echo Something went wrong. Nothing was pushed. Tell Claude what the window says.
pause
