# Qualtrics Build Sheet — full survey flow

Build the blocks in this order. Only the 4 scenario questions use JavaScript (already done).
Everything below is standard Qualtrics — copy the text and choices exactly.

Final block order:
1. Eligibility → 2. Consent → 3. Instructions → 4. Scenario 1–4 (JS, done) →
5. Post-activity → 6. Demographics → 7. Thank-you

---

## BLOCK 1 — Eligibility

**Question 1** · type: Multiple Choice (single answer)
> Are you currently enrolled as a student at Penn State University?
- Yes
- No

**Question 2** · type: Multiple Choice (single answer)
> Are you at least 18 years of age?
- Yes
- No

**Branch logic** (set in Survey Flow, right after this block):
Add a **Branch** → if `Question 1 = No` **OR** `Question 2 = No` → add an **End of Survey**
element inside that branch, with a custom message:
> Thank you for your interest. This study is open only to Penn State students aged 18 or older,
> so you are not eligible to take part.

---

## BLOCK 2 — Consent

**Question 3** · type: Text / Graphic (Descriptive). Paste the consent text:

> **CONSENT FOR PARTICIPATION IN RESEARCH (EXEMPT)** — The Pennsylvania State University
> **Title:** Human and AI Engineering Risk Decisions
> **Faculty Advisor:** Dr. Jeremy M. Gernand, Associate Professor of Environmental Health and
> Safety Engineering, 205 Hosler Building, University Park, PA 16802; jmgernand@psu.edu;
> 814-865-5861.
>
> **Why is this research being done?** This study looks at how decision makers, including
> students and AI models, make risk-related recommendations about technology.
> **What will I be asked to do?** Read a brief set of instructions and then answer a series of
> questions about a risk-related scenario, followed by a few questions about your background.
> **How long?** About 15 minutes, in one sitting.
> **Risks?** No greater than those of everyday life. Some questions may feel unfamiliar; there
> are no right or wrong answers.
> **Benefits?** No direct benefit to you. Results may help technologists use AI tools more
> responsibly.
> **Privacy?** This survey is anonymous. We will not ask for your name, email, student ID, age,
> or gender, and your IP address and location are not recorded. Responses are stored in Penn
> State's password-protected Qualtrics and OneDrive accounts. Because the survey collects no
> identifiers, we cannot remove your answers after you submit them.
> **Payment?** None, and no cost to take part.
> **Voluntary?** Taking part is voluntary. You may skip any question and stop at any time by
> closing your browser, with no effect on your grades or standing. You must be 18 or older.
> **Questions?** Study: Dr. Jeremy Gernand (jmgernand@psu.edu, 814-865-5861). Your rights as a
> participant: Penn State Office for Research Protections, 814-865-1775, orp@psu.edu.
> By selecting "I Agree" you indicate that you have read this form and voluntarily agree to
> take part.

**Question 4** · type: Multiple Choice (single answer)
> Do you agree to take part in this research?
- I Agree
- I Do Not Agree

**Branch logic** (Survey Flow, after this block):
Add a **Branch** → if `Question 4 = I Do Not Agree` → **End of Survey** with message:
> You chose not to take part, so the survey has ended. No responses were recorded. Thank you.

---

## BLOCK 3 — Instructions

**Question 5** · type: Text / Graphic (Descriptive)
> **How this works.** You will see four short scenarios. In each one you must choose one of two
> options, A or B. Before you choose, you may open up to four information cards describing
> features of the two options — you do not have to open all four. There are no right or wrong
> answers; please choose what you would actually prefer. After the scenarios you will answer a
> few short background questions. The task takes about 15 minutes, and your responses are
> anonymous.

---

## BLOCK 4 — Scenarios (already built)

Your four Text/Graphic questions with the JavaScript, each on its own page
(`SCENARIO_INDEX` = 0, 1, 2, 3), writing to embedded fields `S1_data`–`S4_data`.
Keep the page breaks between them.

---

## BLOCK 5 — Post-activity question

**Question 6** · type: Multiple Choice (single answer, horizontal) — or a 1–7 Slider
> When the odds were described vaguely, how much did you focus on what could go wrong?
> (1 = not at all, 7 = a great deal)
- 1
- 2
- 3
- 4
- 5
- 6
- 7

---

## BLOCK 6 — Demographics

**Question 7** · Multiple Choice (single)
> Which best describes your major?
- Engineering
- Computer Science, IST, Data Science
- Math or Statistics
- Natural Science
- Social Science
- Other

**Question 8** · Multiple Choice (single)
> What is your class standing?
- Graduate
- 5th year or more
- 4th year
- 3rd year
- 1st or 2nd year

**Question 9** · Multiple Choice (single)
> Have you taken a course in risk analysis or risk management?
- Yes
- No

**Question 10** · Multiple Choice (single)
> How many years of professional experience do you have (including internships or co-ops)?
- None
- 0–0.5 years
- 0.5–1.0 years
- 1.0–2.0 years
- More than 2.0 years

---

## BLOCK 7 — Thank-you

**Question 11** · type: Text / Graphic (Descriptive)
> **Thank you.** Your responses have been recorded.
>
> A free gift ($5 Starbucks card) is available to the first 100 participants as a
> representation of our gratitude for completing this activity. Send an email to
> **risk-exp@psu.edu** from your official PSU email address, including the date that you
> completed this activity.
>
> Questions? Contact Dr. Jeremy Gernand (jmgernand@psu.edu). Questions about your rights as a
> research participant: Penn State Office for Research Protections, 814-865-1775, orp@psu.edu.

---

## CRITICAL — Survey Options

Survey → **Survey Options** (or Settings):
- **Security → Anonymize responses: ON** (and ensure "record IP / location" is OFF).
  Your consent form promises no IP or location is collected — this setting makes that true.
- **Back button:** optional; leave off so people don't re-open cards after choosing.
- **Prevent multiple submissions / ballot-box stuffing:** optional, your call.

## Test before launch
Preview the whole thing: eligibility → consent → instructions → 4 scenarios → post-activity →
demographics → thank-you. Try a "No" on eligibility and "I Do Not Agree" on consent to confirm
both end the survey. Then check Data & Analysis shows `S1_data`–`S4_data` with JSON.
