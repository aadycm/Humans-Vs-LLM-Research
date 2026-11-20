"""
Writes two paraphrases of each original scenario (Q1-Q4) with Claude, then checks them automatically.
Output: data/paraphrases.json (with "approved": false) and logs/paraphrase_check.txt.
After reading every paraphrase yourself, set "approved": true in data/paraphrases.json.
Run: python code/make_paraphrases.py   (needs ANTHROPIC_API_KEY in .env and "paraphraser" in models.json)
"""
import json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)   # repo root
sys.path.insert(0, HERE)
import run_llm as base
from run_llm_v2 import ENV, http

GAIN_WORDS = ("save", "saved", "saving", "kept", "keep", "keeping", "preserve", "preserved", "preserving", "retain", "retained")
LOSS_WORDS = ("lost", "lose", "losing", "loss", "die", "dies", "die.", "destroyed")

PROMPT = """Rewrite the decision scenario below in two different ways, as two separate versions.

Rules for both versions:
- Keep every number exactly as written, in the same digits and symbols (for example 600, $600,000, 1-in-3, 33%, 10%, 50%). Do not add or remove any number.
- Keep both options and exactly what each one means.
- {frame_rule}
- Keep the same level of uncertainty about the odds. Do not make the odds sound more or less certain.
- Use plain, neutral language. Do not add facts, emotion or advice.
- The two versions must be worded differently from the original and from each other.

Original:
INTRO: {intro}
SAFE OPTION: {safe}
RISKY OPTION: {risky}

Return only JSON in this exact form, with no other text:
{{"p1": {{"intro": "...", "safe": "...", "risky": "..."}}, "p2": {{"intro": "...", "safe": "...", "risky": "..."}}}}
The safe and risky texts must be lowercase-first clauses that can follow "Option A: " like the originals."""

FRAME_RULE = {
 "gain": "Describe the outcomes only in terms of what is saved or kept. Do not use words like lost, lose, die or loss.",
 "loss": "Describe the outcomes only in terms of what is lost. Do not use words like saved, kept, preserved or saving.",
}

def numbers(t):
    t = t.replace(",", "")
    return sorted(re.findall(r"\d+(?:\.\d+)?", t))

def words(t):
    return set(re.findall(r"[a-z]+", t.lower()))

def main():
    cfg = json.load(open(os.path.join(HERE, "models.json"), encoding="utf-8"))
    model = cfg.get("paraphraser", "")
    if not model or model.startswith("FILL"): sys.exit('Set "paraphraser" in models.json first.')
    out = {"approved": False, "paraphraser": model}
    report = []
    for s in base.SCENARIOS:
        r = http("https://api.anthropic.com/v1/messages",
                 {"model": model, "max_tokens": 1200, "temperature": 0.7,
                  "messages": [{"role": "user", "content": PROMPT.format(frame_rule=FRAME_RULE[s["frame"]], intro=s["intro"], safe=s["safe"], risky=s["risky"])}]},
                 {"x-api-key": ENV["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01"})
        text = "".join(b.get("text", "") for b in r.get("content", []))
        js = json.loads(text[text.index("{"): text.rindex("}") + 1])
        out[s["id"]] = js
        orig_nums = numbers(s["intro"] + " " + s["safe"] + " " + s["risky"])
        for k in ("p1", "p2"):
            p = js[k]; full = p["intro"] + " " + p["safe"] + " " + p["risky"]
            probs = []
            if numbers(full) != orig_nums: probs.append(f"numbers differ: original {orig_nums} vs {numbers(full)}")
            w = words(full)
            bad = [x for x in (LOSS_WORDS if s["frame"] == "gain" else GAIN_WORDS) if x in w]
            if bad: probs.append(f"opposite-frame words: {bad}")
            if p["safe"].strip().lower() == s["safe"].strip().lower(): probs.append("safe option identical to original")
            report.append(f"{s['id']} {k}: {'OK' if not probs else 'CHECK -> ' + '; '.join(probs)}")
            report.append(f"   intro: {p['intro']}\n   safe:  {p['safe']}\n   risky: {p['risky']}")
    json.dump(out, open(os.path.join(ROOT, "data", "paraphrases.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    open(os.path.join(ROOT, "logs", "paraphrase_check.txt"), "w", encoding="utf-8").write("\n".join(report))
    print("\n".join(report))
    print('\nRead every paraphrase above. If all are fine, set "approved": true in data/paraphrases.json.')

if __name__ == "__main__":
    main()
