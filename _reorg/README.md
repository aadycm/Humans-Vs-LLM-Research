# Gain or loss wording in people and AI models (ENVSE 497)

A research project at Penn State, Fall 2026.
Aadithya Chandramouli, with faculty mentor Dr. Jeremy M. Gernand.

## What this project is about

The same risky choice can be described in two ways. "200 of 600 people are saved for certain" and "400 of 600 people die for certain" mean the same thing, but people often choose differently depending on which one they read. This is called the framing effect.

We gave the same kind of choice to Penn State students and to large language models (GPT, Gemini, Qwen and Llama). Before choosing, they could open a few "information cards" with extra facts about each option. We wanted to know two things:

1. Does the wording change the choice?
2. Does reading more information make the wording matter less?

## The two parts of the study

**Main study (October 2026).** 198 students and three GPT models did four risk scenarios. Each person could open up to 4 of 7 cards. Our planned question was whether loss wording makes people look at more warning-type cards. The data did not support it. The wording did change people's choices, though.

**Follow-up (November 2026).** Six models, run 11,519 times in total. We changed how many cards a model could open (0, 2, 3 or 4), reworded each scenario two more ways, and added "mirrored" versions with the same facts in the opposite wording. With no cards, every model was strongly affected by the wording. With cards, the effect got smaller in most models, but it only dropped below our 10-point line for GPT-4.1 (at 4 cards) and briefly for Qwen3 (at 2 cards). Two models stayed strongly affected. A paper draft on this part is in `paper/`.

## A few words used in this repo

| Word | Meaning |
|---|---|
| Gain wording / loss wording | The scenario talks about what is saved, or about what is lost. |
| Safe option / risky option | A sure outcome, or a gamble that saves everything or nothing. |
| Information cards | Seven short facts about the options (cost, timing, worst case and so on). |
| Card limit | The most cards a model was allowed to open in a run. |
| Wording gap | How much more often the safe option was picked under gain wording than under loss wording, in percentage points. |
| Mirrored scenario | The same facts as an original scenario, written in the opposite wording. |
| Paraphrase | The same scenario written in different sentences, same numbers and same wording type. |
| Swayed / within threshold / inconclusive | Our labels for a wording gap: clearly 10 points or more, clearly under 10 points, or not clear either way. |

## What is in each folder

| Folder | What you will find |
|---|---|
| `paper/` | The paper draft: `paper_source.md` (the text), `main.tex` and `refs.bib` (LaTeX), `main.pdf`, figures, and an Overleaf zip. |
| `code/` | The scripts that ran the models. `run_llm.py` is the main study, `run_llm_v2.py` is the follow-up, `make_paraphrases.py` wrote the reworded scenarios, `models.json` lists the models. |
| `data/` | Every model run, one line per run, with the model's raw replies. `llm_runs.jsonl` is the main study, `llm_runs_v2.jsonl` is the follow-up, `paraphrases.json` holds the reworded scenarios. Short test runs are in `data/test_runs/`. |
| `analysis/` | Analysis code. `analyze_followup.py` makes every follow-up number in the paper, and `figs_paper.py` draws the paper's figures. `analyze_human.py` and `analyze_combined.py` are the main study. `firth.py` and `glmm.py` are small statistics helpers. |
| `results/` | The outputs of the analysis code: `followup/` for the follow-up, `human/` and `combined/` for the main study. |
| `figures/` | Pictures of the results: `paper/` for the paper figures, `main_study/` for the main study. |
| `docs/` | Everything written along the way. `plans/` has the study plans (including the dated follow-up plan), `survey/` has the consent form and survey, `reports/` has the main study reports, `coursework/` has the course assignments. Start with `docs/PROJECT_LOG.md`, which records what was done and in what order. |
| `logs/` | The text the run scripts printed while they ran. |
| `scripts/` | Double-click files for Windows that run the steps above (see below). |

## How to rerun the analysis

You need Python 3 and a few packages:

```
pip install numpy pandas scipy statsmodels matplotlib
```

Then, from the top folder of the repo:

```
python analysis/analyze_followup.py
python analysis/figs_paper.py
```

The first command rebuilds everything in `results/followup/`. The second redraws the figures in `paper/figures/` and `figures/paper/`. On Windows you can double-click `scripts/run_analysis.bat` instead.

The model runs are already saved in `data/`, so you do not need any API keys to rerun the analysis. You only need keys to collect new runs. In that case, put them in a file called `.env` in the top folder (it is never uploaded) and use the run scripts in `scripts/`.

## About the people data

The survey answers are not in this repo. Our IRB plan keeps participant data on Penn State storage. This repo has only summary numbers for people, in `results/human/` and `results/followup/`. When the people data is missing, `analyze_followup.py` skips that part and keeps the saved people results, so everything else still runs.

## Windows scripts

| Script | What it does |
|---|---|
| `scripts/run_analysis.bat` | Rebuilds the follow-up results and the paper figures. |
| `scripts/update_repo.bat` | Saves your changes and pushes them to GitHub. |
| `scripts/run_main_study.bat` | Runs the main study models again (needs an OpenAI key). |
| `scripts/check_models.bat` | Checks which models your keys can reach. |
| `scripts/write_paraphrases.bat` | Writes the reworded scenarios. |
| `scripts/run_followup_test.bat` | A short test of the follow-up runner, about 5 minutes. |
| `scripts/run_followup_full.bat` | The full follow-up run, a few hours. |

## Contact

Aadithya Chandramouli, Penn State. Questions about the study can also go to Dr. Jeremy M. Gernand.
