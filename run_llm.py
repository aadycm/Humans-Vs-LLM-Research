"""
ENVSE 497 - LLM arm runner (follows 03_AI_Prompt_Protocol).
Usage (PowerShell, inside this folder):
    python run_llm.py --test     # 1 run per model x scenario (12 runs) to check everything works
    python run_llm.py            # full run: 30 runs x 4 scenarios x each model (resumes if interrupted)
Reads OPENAI_API_KEY from .env in this folder. The key is never printed or saved anywhere else.
Output: data/llm_runs.jsonl  (one JSON record per run, raw replies included)
No third-party packages needed.
"""
import json, os, random, re, sys, time, urllib.request, urllib.error
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "llm_runs.jsonl")
# GPT-3.5-turbo and GPT-4 were retired by OpenAI before data collection (404 deprecated);
# replaced with gpt-4o-mini and gpt-4.1 (documented protocol deviation, Oct 31 2026).
MODELS = ["gpt-4o-mini", "gpt-4.1", "gpt-4o"]
RUNS = 30
TEMPERATURE = 1.0
CARD_NAMES = ["Cost", "Benefits", "Timing", "Reliability", "Worst case", "Side effects", "Who is affected"]
THREAT = {"Worst case", "Side effects", "Who is affected"}
MAX_OPEN = 4

INSTRUCTION = ("You are a participant in a decision-making study. You will be shown one\n"
"scenario with two options, A and B, and a list of seven information cards.\n"
"First, choose up to FOUR cards you want to open (you may open fewer).\n"
"List them by their exact names, separated by commas. Do not choose an\n"
"option yet. Respond with only the card names.")

# Identical text to the human survey (qualtrics scenario code).
SCENARIOS = [
 dict(id="Q1", frame="gain", ambiguity="precise",
  intro="A community faces an outbreak expected to affect 600 people. You must choose one response program.",
  safe="200 people are saved for certain.",
  risky="a 1-in-3 (about 33%) chance that all 600 are saved, and otherwise no one is saved.",
  cards={"Cost":("Moderate, fixed public-health budget.","Comparable total cost, spent up front."),
         "Benefits":("Guarantees 200 people saved.","Chance to save all 600 people."),
         "Timing":("Takes effect immediately.","Effect is delayed about two weeks."),
         "Reliability":("Outcome is certain.","Depends on an uncertain transmission response."),
         "Worst case":("400 people are not saved.","With about 67% probability, no one is saved."),
         "Side effects":("Mild, well-documented side effects in the treated group.","Unknown side-effect profile if scaled to all 600."),
         "Who is affected":("A known subgroup of 200 people.","The entire population of 600 is exposed to the gamble.")}),
 dict(id="Q2", frame="gain", ambiguity="ambiguous",
  intro="An organization can protect part of a $600,000 reserve fund that is at risk.",
  safe="$200,000 is preserved for certain.",
  risky="an unknown chance—plausibly between 10% and 50%—that the full $600,000 is preserved, and otherwise none is preserved.",
  cards={"Cost":("Low administrative cost.","Moderate transaction cost."),
         "Benefits":("Secures $200,000.","Chance to secure the full $600,000."),
         "Timing":("Settled this quarter.","Resolves next fiscal year."),
         "Reliability":("Guaranteed outcome.","Probability is not precisely known (est. 10–50%)."),
         "Worst case":("$400,000 is lost.","Likely (est. 50–90%) that the full $600,000 is lost."),
         "Side effects":("Minor short-term liquidity constraint.","Possible covenant breach if the gamble fails."),
         "Who is affected":("The reserve fund only.","The reserve plus dependent operating accounts.")}),
 dict(id="Q3", frame="loss", ambiguity="precise",
  intro="A storm threatens 600 units of municipal equipment.",
  safe="400 units are lost for certain.",
  risky="a 1-in-3 (about 33%) chance that nothing is lost, and otherwise all 600 units are lost.",
  cards={"Cost":("Fixed repair cost.","Comparable cost, contingent on the outcome."),
         "Benefits":("Retains 200 units.","Chance to retain all 600 units."),
         "Timing":("Completed before the storm.","Outcome known only after the storm."),
         "Reliability":("Outcome is certain.","A 1-in-3 chance of success."),
         "Worst case":("400 units are lost.","A 2-in-3 chance that all 600 units are lost."),
         "Side effects":("Service disruption in the repaired zones.","Cascading outages if all units are lost."),
         "Who is affected":("Identified districts.","The entire municipality is at risk.")}),
 dict(id="Q4", frame="loss", ambiguity="ambiguous",
  intro="A wildfire threatens 600 hectares of protected forest.",
  safe="400 hectares are lost for certain.",
  risky="an unknown chance—plausibly between 10% and 50%—that no hectares are lost, and otherwise all 600 are lost.",
  cards={"Cost":("Fixed suppression cost.","Variable, weather-dependent cost."),
         "Benefits":("Saves 200 hectares.","Chance to save all 600 hectares."),
         "Timing":("Crews deploy now.","Depends on a wind shift; timing uncertain."),
         "Reliability":("Outcome is certain.","Probability is not precisely known (est. 10–50%)."),
         "Worst case":("400 hectares are lost.","Likely (est. 50–90%) that all 600 hectares are lost."),
         "Side effects":("Smoke impact in one valley.","Watershed and habitat loss if all burns."),
         "Who is affected":("One forest tract.","Adjacent tracts and the downstream water supply.")}),
]

def load_key():
    p = os.path.join(HERE, ".env")
    with open(p, encoding="utf-8-sig") as f:
        for line in f:
            if line.strip().startswith("OPENAI_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("OPENAI_API_KEY not found in .env")

KEY = load_key()

def api(path, payload=None, tries=6):
    url = "https://api.openai.com/v1/" + path
    data = json.dumps(payload).encode() if payload is not None else None
    for t in range(tries):
        req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
              headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and t < tries - 1:
                time.sleep(2 ** t + random.random()); continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError) as e:
            if t < tries - 1: time.sleep(2 ** t); continue
            raise

def chat(model, messages):
    r = api("chat/completions", {"model": model, "messages": messages, "temperature": TEMPERATURE})
    return r["choices"][0]["message"]["content"] or "", r.get("model", model)

def parse_cards(text):
    found = []
    low = text.lower()
    hits = []
    for c in CARD_NAMES:
        i = low.find(c.lower())
        if i >= 0: hits.append((i, c))
    for _, c in sorted(hits):
        if c not in found: found.append(c)
    return found

def parse_choice(text):
    m = re.findall(r"\b([AB])\b", text.strip().upper())
    return m[0] if len(set(m)) == 1 and m else None

def one_run(model, s, run):
    rng = random.Random()
    safe_is_A = rng.random() < 0.5
    order = CARD_NAMES[:]; rng.shuffle(order)
    optA, optB = (s["safe"], s["risky"]) if safe_is_A else (s["risky"], s["safe"])
    scen = (f"{s['intro']}\nOption A: {optA[0].upper() + optA[1:]}\nOption B: {optB[0].upper() + optB[1:]}\n\n"
            f"Available cards: {' | '.join(order)}")
    msgs = [{"role": "system", "content": INSTRUCTION}, {"role": "user", "content": scen}]
    raw1, served = chat(model, msgs)
    cards = parse_cards(raw1); retried = False
    if not cards:
        retried = True
        msgs2 = msgs + [{"role": "assistant", "content": raw1},
                        {"role": "user", "content": "Please respond with only the names of up to four cards from the list, separated by commas."}]
        raw1b, _ = chat(model, msgs2); raw1 += " || RETRY: " + raw1b; cards = parse_cards(raw1b)
    over = len(cards) > MAX_OPEN
    cards = cards[:MAX_OPEN]
    lines = []
    for c in cards:
        a, b = s["cards"][c] if safe_is_A else s["cards"][c][::-1]
        lines.append(f"{c} - Option A: {a} Option B: {b}")
    opened = "\n".join(lines) if lines else "(no cards opened)"
    msgs3 = msgs + [{"role": "assistant", "content": raw1},
                    {"role": "user", "content": f"Here are the cards you opened:\n{opened}\n\nNow choose one option. Respond with only \"A\" or \"B\"."}]
    raw2, _ = chat(model, msgs3)
    ch = parse_choice(raw2)
    if ch is None:
        retried = True
        raw2b, _ = chat(model, msgs3 + [{"role": "assistant", "content": raw2}, {"role": "user", "content": "Respond with only the single letter A or B."}])
        raw2 += " || RETRY: " + raw2b; ch = parse_choice(raw2b)
    choice = None if ch is None else ("safe" if (ch == "A") == safe_is_A else "risky")
    nT = sum(c in THREAT for c in cards)
    return dict(model=model, served_model=served, scenario_id=s["id"], frame=s["frame"], ambiguity=s["ambiguity"],
                run=run, temperature=TEMPERATURE, safe_label="A" if safe_is_A else "B", card_order=order,
                cards_opened=cards, n_cards_opened=len(cards), n_threat_cards=nT,
                threat_share=(nT / len(cards)) if cards else None, over_limit=over,
                choice_letter=ch, choice=choice, valid=bool(cards) and ch is not None, retried=retried,
                raw_cards=raw1, raw_choice=raw2, ts=datetime.now(timezone.utc).isoformat())

def main():
    test = "--test" in sys.argv
    runs = 1 if test else RUNS
    out = OUT.replace(".jsonl", "_test.jsonl") if test else OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    try:
        avail = {m["id"] for m in api("models")["data"]}
    except Exception as e:
        sys.exit(f"Could not reach OpenAI: {e}")
    models, missing = [], []
    for m in MODELS:
        try:
            api("chat/completions", {"model": m, "messages": [{"role": "user", "content": "Reply OK"}], "max_tokens": 2})
            models.append(m)
        except Exception as e:
            missing.append(f"{m} ({str(e)[:60]})")
    if missing: print("NOT AVAILABLE on this account (skipped):", ", ".join(missing))
    print("Running models:", ", ".join(models))
    done = set()
    if os.path.exists(out):
        with open(out, encoding="utf-8") as f:
            for line in f:
                r = json.loads(line); done.add((r["model"], r["scenario_id"], r["run"]))
    jobs = [(m, s, k) for m in models for s in SCENARIOS for k in range(1, runs + 1) if (m, s["id"], k) not in done]
    random.shuffle(jobs)
    print(f"{len(done)} already done, {len(jobs)} to run.")
    n_bad = 0
    with open(out, "a", encoding="utf-8") as f:
        for i, (m, s, k) in enumerate(jobs, 1):
            try:
                rec = one_run(m, s, k)
            except Exception as e:
                print(f"[{i}/{len(jobs)}] {m} {s['id']} run {k}: ERROR {e}"); n_bad += 1
                if n_bad > 10: sys.exit("Too many errors, stopping. Re-run later to resume.")
                continue
            f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
            print(f"[{i}/{len(jobs)}] {m} {s['id']} run {k}: cards={rec['cards_opened']} choice={rec['choice']}")
    print("DONE. Output:", out)

if __name__ == "__main__":
    main()
