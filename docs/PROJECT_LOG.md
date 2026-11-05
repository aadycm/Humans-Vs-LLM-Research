# Project log: Framing and Ambiguous Risk in Humans and LLMs (ENVSE 497, Fall 2026)

Author: Aadithya Chandramouli. Faculty mentor: Dr. Jeremy M. Gernand.

This log records what was done, in order, including problems and how they were fixed.

## 1. Course deliverables (planning phase)
| Deliverable | File in `docs/` |
|---|---|
| Literature review | `Literature_Review_Framing_LLMs.docx` |
| Hypothesis and falsifiability criteria | `Hypothesis_and_Falsifiability.docx` |
| Experimental plan (IRB exempt) | `Experimental_Plan_IRB.docx` |
| Consent form | `01_Consent_Form.docx` |
| Human survey instrument | `02_Human_Survey_Instrument.docx` |
| LLM prompt protocol | `03_AI_Prompt_Protocol.docx` |
| Statistical analysis plan (written before any data were seen) | `ENVSE497_Statistical_Analysis_Plan.docx` |

**Hypothesis.** Under ambiguous odds, loss framing raises the share of threat-relevant information people examine, and this effect is larger in humans than in LLMs.
**Success criteria (pre-set).** (1) Human loss-vs-gain effect on threat-card share under ambiguity has a 95% CI above zero; (2) the human-minus-LLM difference in that effect has a 95% CI above zero. Both required.

## 2. Building the survey (Qualtrics, Oct 2026)
- Survey: Penn State Qualtrics, combined with classmate Danah Algannas's study (her part follows mine).
- Flow: eligibility (Penn State student, 18+) → consent → instructions → 4 scenarios → post-task item → demographics → thank-you. Non-eligible or non-consenting respondents are ended and flagged *Screened-Out*. Responses anonymized (no IP/location), as the consent form promises.
- The information board is custom JavaScript (`docs/qualtrics_scenario_code_textentry.js`): 7 cards, open up to 4, card order and A/B position randomized per scenario, one JSON record saved per scenario.

**Problems found during testing and fixes**
1. *JavaScript embedded data never saved.* In Qualtrics' new survey-taking engine, `setEmbeddedData` from JavaScript does not persist. Fix: each scenario became a Text Entry question with a hidden text box, and the script writes the JSON into it.
2. *Hidden box still empty.* The box is a React-controlled input, so assigning `.value` was ignored. Fix: use the native value setter and fire `input`/`change` events.
3. *Condition labels sometimes blank (Danah's randomizers).* Each randomizer held 4 separate items (block, label, block, label) and showed 1, so a block could appear without its label. Fix: wrap each block with its label in a Group so the randomizer picks 1 of 2 groups. Verified with exports covering all four combinations.
4. Smaller fixes in the shared survey: duplicate export tags, a single `condition` field being overwritten (split into `condition1`/`condition2`), a stray paragraph, a mis-tagged question.

Lesson: preview runs plus a real **data export** before launch caught every one of these.

## 3. Human data collection (Oct 23 to 27, 2026)
- 212 complete, eligible, consenting responses; 204 of them arrived on Oct 27, the day extra credit was announced in class (busiest hour 1 to 2 pm).
- Extra credit was handled outside the survey so responses stay anonymous.
- Exclusion (pre-set): finished in under one-third of the median duration (126 s) → 14 removed → **198 participants, 792 decisions**.
- Sample: 79% first- or second-year students; majors CS/IST/DS 58, Engineering 51, Math/Stats 13, Natural Science 10, Social Science 4, Other 62; 13% had a risk course; 66% no work experience.
- Median completion 6.7 min (consent form estimated ~15 min); 15 people left the survey open over an hour.
- Raw human data is **not** in this repository (IRB plan: participant data stays on Penn State storage). Only aggregates are under `results/human/`.

## 4. LLM data collection (Oct 31, 2026)
- Runner: `run_llm.py` (Python standard library only), launched with `RUN_ME.bat`. Reads the API key from a local `.env` that is git-ignored and never printed.
- Same 4 scenarios and 7 cards as the survey; 30 fresh-context runs per scenario per model; temperature 1.0; card order and A/B label randomized each run; raw replies logged.
- **Deviation:** OpenAI had retired GPT-3.5-turbo and GPT-4 (the test run returned "model deprecated"), so they were replaced with **GPT-4o-mini** and **GPT-4.1**; GPT-4o kept.
- Result: 360 of 360 runs usable, 30 per model x scenario, no retries. One GPT-4o reply also named a non-existent card ("Probability"), which was ignored (3 cards kept).
- Output: `data/llm_runs.jsonl`.

## 5. Analysis
- Code in `analysis/`. Human: random-intercept binomial GLMM (threat cards out of cards opened) and logistic GLMM (safe choice), fitted by maximum likelihood with Gauss-Hermite quadrature. LLM: Firth-penalized logistic regression, needed because two models chose "safe" almost every time.
- **Deviation:** the plan named R (lme4); analysis was run in Python and cross-checked against statsmodels GLM, GEE and a variational-Bayes mixed model.
- **Independent check:** a separate analysis re-derived every number from the raw data without seeing this code or its results; all estimates matched.

## 6. Results
| | Humans (n = 198) | GPT-4o-mini | GPT-4.1 | GPT-4o |
|---|---|---|---|---|
| Threat share, ambiguous gain → loss | 48% → 49% | 40% → 53% | 46% → 50% | 35% → 37% |
| Safe choice, gain wording | 67% | 60/60 (100%) | 60/60 | 60/60 |
| Safe choice, loss wording | 56% | 24/60 (40%) | 59/60 | 59/60 |
| Opened all 4 cards | 44% of decisions | 120/120 | 120/120 | 119/120 |

- **Hypothesis not supported.** Criterion 1: OR 1.07 (95% CI 0.80 to 1.43). Criterion 2: human minus LLM OR 0.83 (0.55 to 1.25), wrong direction.
- Framing changed **choices** but not **information search** in people (ambiguous odds: 73% → 58% safe; OR 0.43).
- LLMs differ from people in two directions: GPT-4.1 and GPT-4o are uniformly risk-averse; GPT-4o-mini over-reacts to loss wording. All models nearly always open Worst case and Reliability.
- Engagement fell across the fixed scenario order: no cards opened 13% → 53%, median decision time 55 s → 16 s.

Reports: `docs/ENVSE497_Human_Results_Summary.docx`, `docs/ENVSE497_Human_Results_Report.docx`, `docs/ENVSE497_Human_vs_LLM_Results.docx`.

## 7. Limitations
1. Fixed scenario order and fixed topic per condition: fatigue and topic are confounded with condition (human data only; each LLM run is a fresh conversation).
2. One scenario per condition.
3. Convenience sample from one recruitment channel, mostly early-year students; hypothetical, unincentivized choices.
4. Model substitution; LLMs nearly always used all 4 cards, so their search is not on the same footing as people's.
5. Near-unanimous LLM choices give wide confidence intervals.

## 8. Presentation and next steps
- Data-collection presentation (Nov 4, 2026): slide deck "ENVSE 497 Data Collection Review"; script in `docs/presentation_script.md`.
- Dr. Gernand is open to extending this into a publication, with or without new scenarios, after reading a full draft. Next: write the full draft paper (framing: search vs. choice, and human-LLM differences), with the hypothesis rejection reported plainly.
