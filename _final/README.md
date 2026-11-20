# Does more information make AI models less swayed by wording?

This repo has the code, model runs and analysis for our preprint:

**Information Access and Gain-Loss Framing in Six Large Language Models and Human Decision Makers**
Aadithya Chandramouli and Jeremy M. Gernand, The Pennsylvania State University

The paper itself is in `paper/main.pdf`.

## The idea in short

You can describe the same risky choice in two ways. "200 of 600 people are saved for certain" and "400 of 600 people will die for certain" mean the same thing. People still tend to pick the sure option more often when they read the first version. This is called the framing effect.

We wanted to know two things about AI models:

1. Are they swayed by this kind of wording?
2. If they can read more about each option first, are they swayed less?

So we gave six models (GPT-4.1, GPT-4o, GPT-4o-mini, Gemini 2.5 Flash, Qwen3 235B and Llama 4 Maverick) four risky choices. Before choosing, a model could open 0, 2, 3 or 4 of seven short information cards, like cost, timing or the worst case. We also ran 198 Penn State students on the same task.

## What we found

- With no cards, every model was swayed a lot by the wording. The share picking the safe option dropped by 27 to 79 percentage points when the choice was worded as a loss.
- With cards, the effect was smaller in most models, but it rarely got below the 10-point line we set. GPT-4.1 got there at 4 cards and Qwen3 only at 2 cards. GPT-4o-mini and Llama 4 Maverick stayed strongly affected.
- For two models, opening more cards went with a bigger effect, not a smaller one.
- Most of the cards make the risky option look worse, so part of the drop may just be the cards pushing models toward the safe choice. The paper explains this and the other limits.

## What is in each folder

| Folder | What is in it |
|---|---|
| `paper/` | The paper. `main.pdf` is the finished version. `paper_source.md` is the text, `build_paper.py` turns it into `main.tex`, and `refs.bib` has the references. `paper_overleaf.zip` opens in Overleaf. |
| `code/` | The scripts that ran the models. `run_llm.py` ran the first study, `run_llm_v2.py` ran the follow-up with all six models, and `make_paraphrases.py` made the reworded scenarios. `models.json` lists the models. The scenarios, cards and prompts are written out inside these scripts. |
| `data/` | Every model run, one per line, with the model's raw replies. `llm_runs.jsonl` is the first study, `llm_runs_v2.jsonl` is the follow-up, and `paraphrases.json` has the reworded scenarios. |
| `analysis/` | The analysis code. `analyze_followup.py` makes most of the numbers in the paper, `paper_extras.py` makes the rest (run it second), and `figs_paper.py` draws the paper's figures. `analyze_human.py` and `analyze_combined.py` are from the first study. `firth.py` and `glmm.py` are small statistics helpers. |
| `results/` | What the analysis code produces. `followup/` is for the paper, and `human/` and `combined/` are from the first study. |
| `figures/` | Pictures of the results. `paper/` has the paper's figures. |
| `docs/` | Notes and plans from along the way. `plans/` has the study plans, including the written follow-up plan. `survey/` has the consent form and survey. `PROJECT_LOG.md` lists what we did and in what order. |
| `scripts/` | Double-click files for Windows (listed below). |

## How to rerun the numbers

You need Python 3 and these packages:

```
pip install numpy pandas scipy statsmodels matplotlib
```

Then, from the top folder:

```
python analysis/analyze_followup.py
python analysis/paper_extras.py
python analysis/figs_paper.py
```

The first two commands rebuild everything in `results/followup/`. The third redraws the figures. On Windows you can double-click `scripts/run_analysis.bat` instead.

All the model runs are already saved in `data/`, so you don't need any API keys to redo the analysis. You only need keys if you want to collect new runs. For that, put them in a file called `.env` in the top folder. That file is never uploaded.

## About the student data

The students' individual survey answers are not in this repo, to protect the participants. The repo has only the summary numbers for people, in `results/human/` and `results/followup/`. If the survey file is missing, `analyze_followup.py` skips the people part and keeps the saved results, so everything else still runs.

## Windows scripts

| Script | What it does |
|---|---|
| `scripts/run_analysis.bat` | Rebuilds the results and figures. |
| `scripts/update_repo.bat` | Saves your changes and pushes them to GitHub. |
| `scripts/run_main_study.bat` | Runs the first study again (needs an OpenAI key). |
| `scripts/check_models.bat` | Checks which models your keys can reach. |
| `scripts/write_paraphrases.bat` | Makes the reworded scenarios. |
| `scripts/run_followup_test.bat` | A short test of the follow-up, about 5 minutes. |
| `scripts/run_followup_full.bat` | The full follow-up run. This takes a few hours. |

## Contact

Aadithya Chandramouli, Penn State. You can also reach Dr. Jeremy M. Gernand with questions about the study.
