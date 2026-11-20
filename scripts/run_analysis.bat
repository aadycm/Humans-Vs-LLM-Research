@echo off
cd /d "%~dp0.."
echo Rebuilding the follow-up results and the paper figures...
python analysis\analyze_followup.py
python analysis\paper_extras.py
python analysis\figs_paper.py
echo.
echo DONE - results are in results\followup and figures are in figures\paper.
pause
