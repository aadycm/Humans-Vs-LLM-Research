# Framing and Ambiguous Risk in Humans and LLMs (ENVSE 497)

Semester research project, Penn State ENVSE 497 (Fall 2026). Faculty mentor: Dr. Jeremy M. Gernand.
Author: Aadithya Chandramouli.

**Research question.** Under ambiguous risk, how does a scenario's initial framing (gain vs. loss) shape
the information that humans and large language models prioritize before deciding?

**Hypothesis.** Under ambiguous odds, loss framing increases the share of threat-relevant information
people examine more than it does in LLMs (see `docs/Hypothesis_and_Falsifiability.docx`).

## Design
- 2 (Frame: gain/loss) × 2 (Ambiguity: precise "1 in 3" / ambiguous "10–50%") within-subjects; four scenarios
  (public health, financial reserves, infrastructure, wildfire), safe vs. risky option of ~equal expected value.
- Information board: open up to 4 of 7 cards before choosing. Threat cards: Worst case, Side effects, Who is affected.
- **Human arm:** anonymous Qualtrics survey of Penn State students (Oct 23–27, 2026), n = 198 after exclusions.
- **LLM arm:** identical scenarios and cards, 30 fresh-context runs per scenario per model, temperature 1.0,
  card order and A/B position randomized every run (`run_llm.py`, protocol in `docs/03_AI_Prompt_Protocol.docx`).

## Repository layout
| Path | Contents |
|---|---|
| `run_llm.py`, `RUN_ME.bat` | LLM runner (stdlib only; reads `OPENAI_API_KEY` from a local `.env` that is git-ignored) |
| `data/llm_runs.jsonl` | Every LLM run, including raw model replies |
| `analysis/` | Analysis code: `analyze_human.py`, `analyze_combined.py`, mixed-model (`glmm.py`) and Firth (`firth.py`) helpers, figure scripts |
| `results/human/` | Aggregate human results only (cell summaries, model contrasts) |
| `results/combined/` | Human vs. LLM results, descriptives, figures |
| `figures/` | Figures used in reports |
| `docs/PROJECT_LOG.md` | **Start here:** full record of what was done, problems and fixes, results, limitations |
| `docs/` | Literature review, hypothesis, experimental plan, consent form, survey instrument, prompt protocol, statistical analysis plan, results reports, Qualtrics task code |

## Data policy
Raw human responses are **not** in this repository. The IRB-reviewed plan stores participant data only on
Penn State systems, so only aggregate human results are published here. LLM data contains no human subjects
and is included in full.

## Deviations from the pre-registered plan
1. **Models.** The plan named GPT-3.5, GPT-4 and GPT-4o. OpenAI retired GPT-3.5-turbo and GPT-4 before the LLM
   arm was run (API returned "model deprecated"), so they were replaced with **GPT-4o-mini** and **GPT-4.1**;
   GPT-4o was kept. Served model snapshots are logged in every record.
2. **Software.** The plan named R (lme4). Analyses were run in Python with an equivalent maximum-likelihood
   random-intercept binomial GLMM (Gauss–Hermite quadrature), cross-checked against statsmodels GLM, GEE and
   variational-Bayes mixed GLM.
3. **LLM choice models.** Because LLMs chose the safe option almost every time, standard logistic estimates
   do not exist for them (complete separation); LLM effects use Firth-penalized logistic regression.
4. **Sample size.** The plan targeted 50 participants; 198 were analyzed after exclusions.
5. **One malformed LLM reply.** In one GPT-4o run the model also named a non-existent card ("Probability"); it was ignored and the run kept with three cards (negligible effect).
6. **Scenario order.** In the deployed survey each scenario domain was tied to one condition and shown in a
   fixed order, so frame/ambiguity main effects are confounded with domain and position (see reports). Human-vs-LLM comparisons on identical items remove scenario-content differences, but not order/fatigue effects, which apply only to humans.

## Main results
- **Hypothesis not supported.** Under ambiguous odds, loss framing did not raise human threat-card prioritization (OR 1.07, 95% CI 0.80–1.43), and the human-minus-LLM difference was negative and non-significant (OR 0.83, 0.55–1.25).
- **Search style differs.** LLMs opened all four cards in 359/360 runs and almost always chose *Worst case* and *Reliability*; humans opened each card in ~41–57% of decisions and no cards in 34%.
- **Choices differ most.** Humans: 73% → 58% safe (gain → loss, ambiguous). GPT-4.1 and GPT-4o: safe in 119/120 runs each (no framing effect). GPT-4o-mini: 100% → 40% safe (strong framing effect).
- All estimates were re-derived independently from raw data by a separate analysis and matched.

## Reproduce
```
pip install numpy pandas scipy statsmodels matplotlib
python analysis/analyze_combined.py data/human/aadithya_long.csv data/human/aadithya_data.csv data/llm_runs.jsonl results/combined
python analysis/figs_combined.py results/combined
```
(Human CSVs are available from the author on Penn State storage.)
