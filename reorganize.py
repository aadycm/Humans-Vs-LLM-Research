# one time tidy up of the repo  moves files into folders with git mv so history is kept
# run it from REORGANIZE.bat  it is safe to run again  anything already moved is skipped
import os,shutil,subprocess,sys
ROOT=os.path.dirname(os.path.abspath(__file__)); os.chdir(ROOT)
GIT="--no-git" not in sys.argv

MOVES={
 # code
 "run_llm.py":"code/run_llm.py","run_llm_v2.py":"code/run_llm_v2.py","make_paraphrases.py":"code/make_paraphrases.py","models.json":"code/models.json",
 # windows launchers
 "RUN_ME.bat":"scripts/run_main_study.bat","PROBE_MODELS.bat":"scripts/check_models.bat","PREP.bat":"scripts/write_paraphrases.bat",
 "TEST_V2.bat":"scripts/run_followup_test.bat","RUN_V2.bat":"scripts/run_followup_full.bat","UPDATE_REPO.bat":"scripts/update_repo.bat",
 # run logs
 "data_full_log.txt":"logs/main_study_run_log.txt","data_test_log.txt":"logs/main_study_test_log.txt",
 "data_v2_full_log.txt":"logs/followup_run_log.txt","data_v2_test_log.txt":"logs/followup_test_log.txt",
 "data_probe_log.txt":"logs/model_check_log.txt","data/available_models.txt":"logs/available_models.txt",
 "push_log.txt":"logs/push_log.txt","repo_log.txt":"logs/repo_log.txt",
 # test runs
 "data/llm_runs_test.jsonl":"data/test_runs/llm_runs_test.jsonl","data/llm_runs_v2_test.jsonl":"data/test_runs/llm_runs_v2_test.jsonl",
 # figures
 "figures/fig1.png":"figures/main_study/fig1_threat_share.png","figures/fig2.png":"figures/main_study/fig2_safe_choice.png","figures/fig3.png":"figures/main_study/fig3_engagement_by_position.png",
 "figures/fig_safe_by_agent.png":"figures/main_study/fig_safe_by_agent.png","figures/fig_threat_by_agent.png":"figures/main_study/fig_threat_by_agent.png",
 # paper
 "paper_overleaf.zip":"paper/paper_overleaf.zip",
 # docs
 "docs/Experimental_Plan_IRB.docx":"docs/plans/Experimental_Plan_IRB.docx",
 "docs/ENVSE497_Statistical_Analysis_Plan.docx":"docs/plans/ENVSE497_Statistical_Analysis_Plan.docx",
 "docs/ENVSE497_FollowUp_Plan.pdf":"docs/plans/ENVSE497_FollowUp_Plan.pdf",
 "docs/Hypothesis_and_Falsifiability.docx":"docs/plans/Hypothesis_and_Falsifiability.docx",
 "docs/03_AI_Prompt_Protocol.docx":"docs/plans/03_AI_Prompt_Protocol.docx",
 "docs/01_Consent_Form.docx":"docs/survey/01_Consent_Form.docx","docs/02_Human_Survey_Instrument.docx":"docs/survey/02_Human_Survey_Instrument.docx",
 "docs/ENVSE497_survey_import.txt":"docs/survey/ENVSE497_survey_import.txt","docs/Qualtrics_Build_Sheet.md":"docs/survey/Qualtrics_Build_Sheet.md",
 "docs/qualtrics_scenario_code.txt":"docs/survey/qualtrics_scenario_code.txt","docs/qualtrics_scenario_code_textentry.js":"docs/survey/qualtrics_scenario_code_textentry.js",
 "docs/ENVSE497_Human_Results_Report.docx":"docs/reports/ENVSE497_Human_Results_Report.docx","docs/ENVSE497_Human_Results_Summary.docx":"docs/reports/ENVSE497_Human_Results_Summary.docx",
 "docs/ENVSE497_Human_vs_LLM_Results.docx":"docs/reports/ENVSE497_Human_vs_LLM_Results.docx",
 "docs/Critical_Review_LLMs_Social_Decisions.docx":"docs/coursework/Critical_Review_LLMs_Social_Decisions.docx",
 "docs/Literature_Review_Framing_LLMs.docx":"docs/coursework/Literature_Review_Framing_LLMs.docx",
 "docs/ENVSE497_Status_Update.pptx":"docs/coursework/ENVSE497_Status_Update.pptx","docs/presentation_script.md":"docs/coursework/presentation_script.md",
 "docs/00_Materials_Index.docx":"docs/coursework/00_Materials_Index.docx",
 "docs/ENVSE497_Experimental_Materials_Combined.pdf":"docs/coursework/ENVSE497_Experimental_Materials_Combined.pdf",
}
# old or superseded files  still in git history if ever needed
REMOVE=["SETUP_REPO.bat","data/llm_runs_v2.jsonl.lock","data/llm_runs_v2_test.jsonl.lock",
 "figures/fig1_models_gap.pdf","figures/fig1_models_gap.png","figures/fig2_people_gap.pdf","figures/fig2_people_gap.png",
 "figures/fig3_original_vs_mirrored.pdf","figures/fig3_original_vs_mirrored.png","figures/fig4_summary_grid.pdf","figures/fig4_summary_grid.png",
 "figures/fig_followup_gap.png","figures/fig_followup_original_vs_mirrored.png","analysis/figs_followup.py"]

def git(*a,check=True):
    r=subprocess.run(["git",*a],capture_output=True,text=True)
    if check and r.returncode: print("git",*a,"->",r.stderr.strip())
    return r
def tracked(p): return GIT and git("ls-files","--error-unmatch",p,check=False).returncode==0

moved=0
for old,new in MOVES.items():
    if not os.path.exists(old): continue
    os.makedirs(os.path.dirname(new),exist_ok=True)
    if os.path.exists(new): os.remove(new)
    if tracked(old): git("mv",old,new)
    else: shutil.move(old,new)
    moved+=1
removed=0
for p in REMOVE:
    if not os.path.exists(p): continue
    if tracked(p): git("rm","-q","--cached",p)
    os.remove(p); removed+=1
# drop in the edited files (new paths in the code  new readme  new launchers)
over=os.path.join(ROOT,"_reorg"); copied=0
if os.path.isdir(over):
    for d,_,fs in os.walk(over):
        for f in fs:
            src=os.path.join(d,f); dst=os.path.relpath(src,over)
            os.makedirs(os.path.dirname(dst) or ".",exist_ok=True); shutil.copyfile(src,dst); copied+=1
    shutil.rmtree(over)
for p in ["__pycache__","code/__pycache__","analysis/__pycache__"]:
    shutil.rmtree(p,ignore_errors=True)
print(f"moved {moved} files, removed {removed} old files, updated {copied} files")
if GIT:
    # github moved the repo to a new name  point the remote at it
    git("remote","set-url","origin","git@github.com:aadycm/Humans-Vs-LLM-Research.git")
    git("add","-A")
    print(git("status","--short").stdout)
