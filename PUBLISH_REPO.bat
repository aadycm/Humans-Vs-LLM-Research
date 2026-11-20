@echo off
cd /d "%~dp0"
if not exist _final\README.md goto nofinal
echo This updates your GitHub repo with the cleaned-up version for the preprint.
echo Your .env file and API keys are not touched and are never uploaded.
echo.
git remote set-url origin git@github.com:aadycm/Humans-Vs-LLM-Research.git
git ls-files > _old_files.txt
if not exist logs mkdir logs
for %%f in (data_full_log.txt data_probe_log.txt data_test_log.txt data_v2_full_log.txt data_v2_test_log.txt push_log.txt repo_log.txt) do if exist %%f move /y %%f logs\ >nul
git rm -r -q --cached . >nul
git --work-tree=_final add -A
if errorlevel 1 goto fail
echo These are the changes going up:
git status --short
echo.
git commit -q -F _commitmsg.txt
if errorlevel 1 goto fail
echo Saved. Press a key to push to GitHub, or close this window to stop here.
pause
git push > logs\push_log.txt 2>&1
type logs\push_log.txt
echo.
echo Tidying this folder to match what is on GitHub...
powershell -NoProfile -Command "$new=git ls-tree -r --name-only HEAD; foreach($f in Get-Content _old_files.txt){ if(-not ($new -contains $f) -and (Test-Path -LiteralPath $f)){ Remove-Item -LiteralPath $f -Force } }"
git reset -q --hard
if exist _reorg rmdir /s /q _reorg
if exist reorganize.py del reorganize.py
if exist REORGANIZE.bat del REORGANIZE.bat
del _old_files.txt
del _commitmsg.txt
rmdir /s /q _final
echo.
echo ALL DONE. Now open the repo on GitHub, go to Settings and make it public.
echo From now on, use scripts\update_repo.bat to push changes.
pause
(goto) 2>nul & del "%~f0"
:nofinal
echo The _final folder is missing, so nothing was changed. Tell Claude.
pause
goto :eof
:fail
echo Something went wrong. Nothing was pushed. Tell Claude what this window says.
pause
