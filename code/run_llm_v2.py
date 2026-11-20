"""
ENVSE 497 - follow-up LLM runs (added after the main study).
Factors: model x card level (0, 2, 3, 4) x wording (original, p1, p2) x 4 scenarios, 30 runs each,
plus mirrored scenarios M1-M4 (same facts, opposite gain/loss wording; original wording only).
The original-wording, 4-card GPT runs from the main study (data/llm_runs.jsonl) are not repeated.

Usage (PowerShell or double-click a .bat in this folder):
    python run_llm_v2.py --probe     # list the models each API key can use -> data/available_models.txt
    python run_llm_v2.py --test      # 1 run per cell for every model (quick check)
    python run_llm_v2.py             # full run; resumes if interrupted
Keys are read from .env in this folder (never printed):
    OPENAI_API_KEY=...  GOOGLE_API_KEY=...  OPENROUTER_API_KEY=...  (TOGETHER_API_KEY / ANTHROPIC_API_KEY optional)
Models are listed in models.json.
"""
import json, os, random, re, sys, time, threading, urllib.request, urllib.error
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace"); sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # repo root  data logs and .env live there
sys.path.insert(0, HERE)
import run_llm as base  # same scenarios, card texts, parsers as the main study

RUNS = 30
LIMITS = [0, 2, 3, 4]   # 0 = no cards: the model reads the scenario and chooses
WORDINGS = ["orig", "p1", "p2"]
TEMPERATURE = 1.0
WORKERS = 6
OUT = os.path.join(ROOT, "data", "llm_runs_v2.jsonl")

# Paraphrases are written by Claude (make_paraphrases.py), checked by script, and approved by hand.
PARA_FILE = os.path.join(ROOT, "data", "paraphrases.json")
def load_para():
    if not os.path.exists(PARA_FILE): return None
    d = json.load(open(PARA_FILE, encoding="utf-8"))
    return d if d.get("approved") is True else None

# Mirrored scenarios: same facts as Q1-Q4, opposite wording. Cards are the same as the base scenario.
MIRROR = {
 "M1": dict(base="Q1", frame="loss", safe="400 people will die for certain.",
            risky="a 1-in-3 (about 33%) chance that nobody dies, and otherwise all 600 people die."),
 "M2": dict(base="Q2", frame="loss", safe="$400,000 is lost for certain.",
            risky="an unknown chance\u2014plausibly between 10% and 50%\u2014that none of the $600,000 is lost, and otherwise all of it is lost."),
 "M3": dict(base="Q3", frame="gain", safe="200 units are saved for certain.",
            risky="a 1-in-3 (about 33%) chance that all 600 units are saved, and otherwise none are saved."),
 "M4": dict(base="Q4", frame="gain", safe="200 hectares are saved for certain.",
            risky="an unknown chance\u2014plausibly between 10% and 50%\u2014that all 600 hectares are saved, and otherwise none are saved."),
}
def mirrored_scenarios():
    out = []
    for mid, m in MIRROR.items():
        b = [x for x in base.SCENARIOS if x["id"] == m["base"]][0]
        out.append(dict(b, id=mid, frame=m["frame"], safe=m["safe"], risky=m["risky"], base=m["base"]))
    return out

WORDS = {1: "ONE", 2: "TWO", 3: "THREE", 4: "FOUR"}

def instruction(limit):
    return ("You are a participant in a decision-making study. You will be shown one\n"
            "scenario with two options, A and B, and a list of seven information cards.\n"
            f"First, choose up to {WORDS[limit]} cards you want to open (you may open fewer).\n"
            "List them by their exact names, separated by commas. Do not choose an\n"
            "option yet. Respond with only the card names.")

def load_env():
    env = {}
    with open(os.path.join(ROOT, ".env"), encoding="utf-8-sig") as f:
        for line in f:
            if "=" in line and not line.strip().startswith("#"):
                k, v = line.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
    return env
ENV = load_env()

def http(url, payload=None, headers=None, tries=8):
    data = json.dumps(payload).encode() if payload is not None else None
    for t in range(tries):
        req = urllib.request.Request(url, data=data, method="POST" if data else "GET",
                                     headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:300]
            if e.code in (429, 500, 502, 503, 504, 529) and t < tries - 1 and "insufficient_quota" not in body:
                try: wait = float(e.headers.get("retry-after") or 0)
                except (TypeError, ValueError): wait = 0
                time.sleep(min(60, max(wait, 2 ** t)) + random.random()); continue
            raise RuntimeError(f"HTTP {e.code}: {body}")
        except (urllib.error.URLError, TimeoutError):
            if t < tries - 1: time.sleep(2 ** t); continue
            raise

# ---- providers: chat(model, system, messages[{role:user|assistant, content}]) -> text
MODEL_EXTRA = {}       # extra request settings per model, from "extra" in models.json
REASONING = {}         # hidden "thinking" tokens each model used (should stay 0)
_rlock = threading.Lock()
def chat_openai(model, system, msgs, base_url="https://api.openai.com/v1", key_name="OPENAI_API_KEY"):
    body = {"model": model, "temperature": TEMPERATURE, "messages": [{"role": "system", "content": system}] + msgs}
    body.update(MODEL_EXTRA.get(model, {}))
    r = http(base_url + "/chat/completions", body, {"Authorization": "Bearer " + ENV[key_name]})
    try: rt = int(((r.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
    except (TypeError, ValueError, AttributeError): rt = 0
    if rt:
        with _rlock: REASONING[model] = REASONING.get(model, 0) + rt
    return r["choices"][0]["message"]["content"] or "", r.get("model", model)
def chat_together(model, system, msgs):
    return chat_openai(model, system, msgs, "https://api.together.xyz/v1", "TOGETHER_API_KEY")
def chat_openrouter(model, system, msgs):
    return chat_openai(model, system, msgs, "https://openrouter.ai/api/v1", "OPENROUTER_API_KEY")
def chat_anthropic(model, system, msgs):
    r = http("https://api.anthropic.com/v1/messages",
             {"model": model, "max_tokens": 300, "temperature": TEMPERATURE, "system": system, "messages": msgs},
             {"x-api-key": ENV["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
    return "".join(b.get("text", "") for b in r.get("content", [])), r.get("model", model)
def chat_google(model, system, msgs):
    contents = [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in msgs]
    r = http(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
             {"systemInstruction": {"parts": [{"text": system}]}, "contents": contents,
              "generationConfig": {"temperature": TEMPERATURE}},
             {"x-goog-api-key": ENV["GOOGLE_API_KEY"]})
    parts = r["candidates"][0].get("content", {}).get("parts", [])
    return "".join(p.get("text", "") for p in parts if not p.get("thought")), r.get("modelVersion", model)
PROVIDERS = {"openai": chat_openai, "anthropic": chat_anthropic, "google": chat_google, "together": chat_together, "openrouter": chat_openrouter}
KEYS = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY", "together": "TOGETHER_API_KEY", "openrouter": "OPENROUTER_API_KEY"}

def probe():
    out = []
    for prov, key in KEYS.items():
        if not ENV.get(key): out.append(f"[{prov}] no {key} in .env"); continue
        try:
            if prov == "openai": ids = [m["id"] for m in http("https://api.openai.com/v1/models", headers={"Authorization": "Bearer " + ENV[key]})["data"]]
            elif prov == "together": r = http("https://api.together.xyz/v1/models", headers={"Authorization": "Bearer " + ENV[key]}); ids = [m["id"] for m in (r if isinstance(r, list) else r.get("data", []))]
            elif prov == "openrouter":
                r = http("https://openrouter.ai/api/v1/models", headers={"Authorization": "Bearer " + ENV[key]})
                def price(m, k):
                    try: return f"${float(m['pricing'][k]) * 1e6:.2f}/M"
                    except Exception: return "?"
                ids = [f"{m['id']}  ({price(m, 'prompt')} in, {price(m, 'completion')} out)"
                       for m in r.get("data", []) if str(m.get("id", "")).startswith(("meta-llama/", "qwen/", "google/gemini"))]
            elif prov == "anthropic": ids = [m["id"] for m in http("https://api.anthropic.com/v1/models?limit=100", headers={"x-api-key": ENV[key], "anthropic-version": "2023-06-01"})["data"]]
            else: ids = [m["name"].split("/")[-1] for m in http("https://generativelanguage.googleapis.com/v1beta/models?pageSize=200", headers={"x-goog-api-key": ENV[key]})["models"]]
            out.append(f"[{prov}] {len(ids)} models:\n  " + "\n  ".join(sorted(ids)))
        except Exception as e:
            out.append(f"[{prov}] ERROR {str(e)[:200]}")
    os.makedirs(os.path.join(ROOT, "logs"), exist_ok=True)
    p = os.path.join(ROOT, "logs", "available_models.txt")
    open(p, "w", encoding="utf-8").write("\n\n".join(out)); print("Wrote", p)

THINK = re.compile(r"<think>.*?</think>", re.S | re.I)
def clean(text):
    """Drop any <think>...</think> reasoning some open models print before the answer."""
    return THINK.sub("", text or "").strip()

def parse_choice(text):
    """A or B. Exact one-letter answers first; otherwise a standalone capital A or B in the original
    text (so the article 'a' is never read as option A). Two different letters -> None (retry)."""
    t = clean(text)
    m = re.fullmatch(r"\W*(?:option\s*)?([AB])\W*", t, re.I)
    if m: return m.group(1).upper()
    hits = set(re.findall(r"(?<![A-Za-z])([AB])(?![A-Za-z])", t))
    return hits.pop() if len(hits) == 1 else None

def parse_cards(text):
    return base.parse_cards(clean(text))

PARA = None
def scenario(s, wording):
    if wording == "orig": return s["intro"], s["safe"], s["risky"]
    p = PARA[s["id"]][wording]; return p["intro"], p["safe"], p["risky"]

def one_run(prov, model, s, wording, limit, run):
    chat = PROVIDERS[prov]
    rng = random.Random(); safe_is_A = rng.random() < 0.5
    order = base.CARD_NAMES[:]; rng.shuffle(order)
    intro, safe, risky = scenario(s, wording)
    optA, optB = (safe, risky) if safe_is_A else (risky, safe)
    scen = (f"{intro}\nOption A: {optA[0].upper() + optA[1:]}\nOption B: {optB[0].upper() + optB[1:]}\n\n"
            f"Available cards: {' | '.join(order)}")
    if limit == 0:
        system = ("You are a participant in a decision-making study. You will be shown one\n"
                  "scenario with two options, A and B. Choose one option. Respond with only \"A\" or \"B\".")
        scen0 = f"{intro}\nOption A: {optA[0].upper() + optA[1:]}\nOption B: {optB[0].upper() + optB[1:]}"
        msgs = [{"role": "user", "content": scen0}]
        raw2, served = chat(model, system, msgs); ch = parse_choice(raw2); retried = False
        if ch is None:
            retried = True
            r, _ = chat(model, system, msgs + [{"role": "assistant", "content": raw2 or "(no answer)"}, {"role": "user", "content": "Respond with only the single letter A or B."}])
            raw2 += " || RETRY: " + r; ch = parse_choice(r)
        choice = None if ch is None else ("safe" if (ch == "A") == safe_is_A else "risky")
        return dict(provider=prov, model=model, served_model=served, scenario_id=s["id"], topic=s.get("base", s["id"]), frame=s["frame"],
                    ambiguity=s["ambiguity"], wording=wording, card_limit=0, run=run, temperature=TEMPERATURE,
                    safe_label="A" if safe_is_A else "B", card_order=[], cards_opened=[], n_cards_opened=0,
                    n_threat_cards=0, threat_share=None, over_limit=False, invalid_names=[], choice_letter=ch,
                    choice=choice, valid=ch is not None, retried=retried, raw_cards="", raw_choice=raw2,
                    ts=datetime.now(timezone.utc).isoformat())
    system = instruction(limit)
    msgs = [{"role": "user", "content": scen}]
    raw1, served = chat(model, system, msgs); cards = parse_cards(raw1); retried = False
    invalid_named = [w.strip(" .;:*-") for w in clean(raw1).replace("\n", ",").split(",") if w.strip(" .;:*-") and not parse_cards(w)]
    if not cards or len(cards) > limit:   # no card named, or an essay naming more cards than allowed: ask again
        retried = True
        m2 = msgs + [{"role": "assistant", "content": raw1 or "(no answer)"},
                     {"role": "user", "content": f"Please respond with only the names of up to {WORDS[limit].lower()} cards from the list, separated by commas."}]
        r, _ = chat(model, system, m2); raw1 += " || RETRY: " + r
        retry_cards = parse_cards(r)
        if retry_cards: cards = retry_cards
    over = len(cards) > limit; cards = cards[:limit]
    lines = []
    for c in cards:
        a, b = s["cards"][c] if safe_is_A else s["cards"][c][::-1]
        lines.append(f"{c} - Option A: {a} Option B: {b}")
    opened = "\n".join(lines) if lines else "(no cards opened)"
    m3 = msgs + [{"role": "assistant", "content": raw1 or "(no answer)"},
                 {"role": "user", "content": f"Here are the cards you opened:\n{opened}\n\nNow choose one option. Respond with only \"A\" or \"B\"."}]
    raw2, _ = chat(model, system, m3); ch = parse_choice(raw2)
    if ch is None:
        retried = True
        r, _ = chat(model, system, m3 + [{"role": "assistant", "content": raw2 or "(no answer)"}, {"role": "user", "content": "Respond with only the single letter A or B."}])
        raw2 += " || RETRY: " + r; ch = parse_choice(r)
    choice = None if ch is None else ("safe" if (ch == "A") == safe_is_A else "risky")
    nT = sum(c in base.THREAT for c in cards)
    return dict(provider=prov, model=model, served_model=served, scenario_id=s["id"], topic=s.get("base", s["id"]), frame=s["frame"], ambiguity=s["ambiguity"],
                wording=wording, card_limit=limit, run=run, temperature=TEMPERATURE,
                safe_label="A" if safe_is_A else "B", card_order=order, cards_opened=cards,
                n_cards_opened=len(cards), n_threat_cards=nT, threat_share=(nT / len(cards)) if cards else None,
                over_limit=over, invalid_names=invalid_named, choice_letter=ch, choice=choice, valid=bool(cards) and ch is not None,
                retried=retried, raw_cards=raw1, raw_choice=raw2, ts=datetime.now(timezone.utc).isoformat())

class Tee:
    """Show output in the window and save it to a log file at the same time."""
    def __init__(self, stream, path):
        self.stream, self.f = stream, open(path, "w", encoding="utf-8")
    def write(self, t):
        try: self.stream.write(t); self.stream.flush()
        except Exception: pass
        self.f.write(t); self.f.flush()
    def flush(self): self.f.flush()

def main():
    if "--log" in sys.argv:
        sys.stdout = sys.stderr = Tee(sys.stdout, os.path.join(ROOT, sys.argv[sys.argv.index("--log") + 1]))
    if "--probe" in sys.argv: return probe()
    global PARA
    PARA = load_para()
    if PARA is None:
        sys.exit("Paraphrases not approved yet: run make_paraphrases.py, review data/paraphrases.json, then set \"approved\": true.")
    test = "--test" in sys.argv
    cfg = json.load(open(os.path.join(HERE, "models.json"), encoding="utf-8"))
    runs = 1 if test else RUNS
    out = OUT.replace(".jsonl", "_test.jsonl") if test else OUT
    os.makedirs(os.path.dirname(out), exist_ok=True)
    lock_file = open(out + ".lock", "a+")   # the OS frees this lock even if the window is closed
    try:
        if os.name == "nt":
            import msvcrt; lock_file.seek(0); msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl; fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        sys.exit("Another run is already going in a different window. Let it finish (or close it) first.")
    if test and os.path.exists(out): os.remove(out)   # every test starts fresh
    _run(cfg, runs, out, test)

def _run(cfg, runs, out, test):
    models = []; skipped = []
    for m in cfg["models"]:
        if m.get("extra"): MODEL_EXTRA[m["model"]] = m["extra"]
        if m["model"].startswith("FILL"): print(f"SKIP {m['provider']}: model not chosen yet in models.json"); continue
        if not ENV.get(KEYS[m["provider"]]): print(f"SKIP {m['model']}: no {KEYS[m['provider']]} in .env"); continue
        try: PROVIDERS[m["provider"]](m["model"], "Reply with the single word OK.", [{"role": "user", "content": "Reply OK"}]); models.append(m)
        except Exception as e: print(f"SKIP {m['model']}: {str(e)[:120]}"); skipped.append(m["model"])
    if not models: sys.exit("No model could be reached. Check the keys in .env and your internet connection.")
    print("Running:", ", ".join(m["model"] for m in models))
    done = set(); bad_lines = 0
    if os.path.exists(out):
        with open(out, "rb") as fb:
            raw = fb.read()
        good = []
        for line in raw.decode("utf-8", errors="replace").splitlines():
            if not line.strip(): continue
            try:
                r = json.loads(line); done.add((r["model"], r["scenario_id"], r["wording"], r["card_limit"], r["run"])); good.append(line)
            except Exception:
                bad_lines += 1
        if bad_lines or (raw and not raw.endswith(b"\n")):
            with open(out, "w", encoding="utf-8") as fw:   # drop a half-written last line from an interrupted run
                fw.write("".join(l + "\n" for l in good))
            print(f"Removed {bad_lines} damaged line(s) left by an interrupted run.")
    jobs = []
    for m in models:
        for s in base.SCENARIOS:
            for w in WORDINGS:
                for L in LIMITS:
                    if m.get("main_study") and w == "orig" and L == 4 and not test: continue  # already in llm_runs.jsonl
                    for k in range(1, runs + 1):
                        if (m["model"], s["id"], w, L, k) not in done: jobs.append((m["provider"], m["model"], s, w, L, k))
        for s in mirrored_scenarios():
            for L in LIMITS:
                for k in range(1, runs + 1):
                    if (m["model"], s["id"], "orig", L, k) not in done: jobs.append((m["provider"], m["model"], s, "orig", L, k))
    random.shuffle(jobs)
    print(f"{len(done)} already done, {len(jobs)} to run.", flush=True)
    lock = threading.Lock(); errors = [0]; ok = [0]; consecutive = [0]
    with open(out, "a", encoding="utf-8") as f, ThreadPoolExecutor(WORKERS) as ex:
        futs = {ex.submit(one_run, *j): j for j in jobs}
        for i, fu in enumerate(as_completed(futs), 1):
            j = futs[fu]
            try:
                rec = fu.result()
                with lock: f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
                ok[0] += 1; consecutive[0] = 0
                if i % 25 == 0 or test: print(f"[{i}/{len(jobs)}] {j[1]} {j[2]['id']} {j[3]} L{j[4]}: {rec['cards_opened']} {rec['choice']}", flush=True)
            except Exception as e:
                errors[0] += 1; consecutive[0] += 1
                print(f"[{i}/{len(jobs)}] {j[1]} {j[2]['id']} {j[3]} L{j[4]} run {j[5]}: ERROR {str(e)[:150]}", flush=True)
                if consecutive[0] >= 40:
                    print("STOPPING: 40 errors in a row (bad key, no internet, or provider down). Fix it and run again; finished runs are kept.", flush=True)
                    for other in futs: other.cancel()
                    ex.shutdown(wait=False, cancel_futures=True)
                    break
    summarize(out, models, runs, test)
    for mm, n in REASONING.items(): print(f"  NOTE: {mm} used {n:,} hidden thinking tokens")
    if skipped: print(f"WARNING: these models could not be reached and were NOT run: {', '.join(skipped)}")
    print(f"DONE. new runs saved={ok[0]}, errors={errors[0]}. Output: {out}. If anything is missing, run again to fill it.")

def summarize(out, models, runs, test):
    """Check every planned cell has the right number of valid runs."""
    cnt = {}; invalid = 0
    for line in open(out, encoding="utf-8"):
        r = json.loads(line)
        k = (r["model"], r["scenario_id"], r["wording"], r["card_limit"])
        cnt[k] = cnt.get(k, 0) + 1; invalid += (not r["valid"])
    missing = []
    for m in models:
        cells = [(s["id"], w, L) for s in base.SCENARIOS for w in WORDINGS for L in LIMITS
                 if not (m.get("main_study") and w == "orig" and L == 4 and not test)]
        cells += [(s["id"], "orig", L) for s in mirrored_scenarios() for L in LIMITS]
        short = [c for c in cells if cnt.get((m["model"],) + c, 0) < runs]
        print(f"  {m['model']}: {len(cells)} cells, {sum(cnt.get((m['model'],) + c, 0) for c in cells)} runs saved, {len(short)} cells not complete")
        missing += short
    print(f"  invalid answers (kept, flagged): {invalid}")
    print("  ALL CELLS COMPLETE" if not missing else f"  {len(missing)} cells still incomplete -> run again")

if __name__ == "__main__":
    main()
