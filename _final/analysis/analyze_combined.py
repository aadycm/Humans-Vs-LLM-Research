"""Combined human + LLM analysis, following ENVSE497_Statistical_Analysis_Plan.
python analyze_combined.py <human_long.csv> <human_wide.csv> <llm_runs.jsonl> <outdir>"""
import sys, os, json, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from glmm import fit_ri_binomial, contrast
hl, hw, lj, out = sys.argv[1:5]; os.makedirs(out, exist_ok=True)
R = {}
# ---- human, same exclusions as human report
w = pd.read_csv(hw, encoding='utf-8-sig'); L = pd.read_csv(hl, encoding='utf-8-sig')
cut = w['Duration (in seconds)'].median() / 3
keep = set(w.loc[w['Duration (in seconds)'] >= cut, 'ResponseId'])
L = L[L.ResponseId.isin(keep)]
H = pd.DataFrame(dict(source='human', unit=L.ResponseId, frame=L.frame, ambiguity=L.ambiguity,
     nOpened=L.nOpened, nThreat=L.nThreat, safe=(L.choice == 'safe').astype(int), cards=L.cardsOpened.fillna('')))
# ---- LLM
rows = [json.loads(x) for x in open(lj, encoding='utf-8')]
M = pd.DataFrame(rows)
R['llm_total_records'] = len(M); R['llm_invalid'] = int((~M.valid).sum()); R['llm_retried'] = int(M.retried.sum())
R['llm_over_limit'] = int(M.over_limit.sum())
R['llm_counts'] = M.groupby(['model', 'scenario_id']).size().unstack().to_dict()
R['served_models'] = M.groupby('model').served_model.unique().apply(list).to_dict()
Mv = M[M.valid]
Ld = pd.DataFrame(dict(source=Mv.model, unit=Mv.model + '_' + Mv.scenario_id + '_' + Mv.run.astype(str),
     frame=Mv.frame, ambiguity=Mv.ambiguity, nOpened=Mv.n_cards_opened, nThreat=Mv.n_threat_cards,
     safe=(Mv.choice == 'safe').astype(int), cards=Mv.cards_opened.apply(';'.join)))
D = pd.concat([H, Ld], ignore_index=True)
D['llm'] = (D.source != 'human').astype(int); D['loss'] = (D.frame == 'loss').astype(int); D['amb'] = (D.ambiguity == 'ambiguous').astype(int)
D['int'] = 1; D['one'] = 1
for a, b in [('loss', 'amb'), ('llm', 'loss'), ('llm', 'amb')]: D[f'{a}_{b}'] = D[a] * D[b]
D['llm_loss_amb'] = D.llm * D.loss * D.amb
D.to_csv(os.path.join(out, 'combined_trials.csv'), index=False)
# ---- descriptives
def cell(d):
    c = d[d.nOpened > 0]
    return pd.Series(dict(n=len(d), zero_cards=(d.nOpened == 0).mean(), mean_opened=d.nOpened.mean(),
        threat_pooled=c.nThreat.sum() / max(c.nOpened.sum(), 1), threat_mean=(c.nThreat / c.nOpened).mean(),
        safe=d.safe.mean()))
desc = D.groupby(['source', 'frame', 'ambiguity']).apply(cell).reset_index()
desc.to_csv(os.path.join(out, 'descriptives.csv'), index=False); R['desc'] = desc.to_dict('records')
cards = ['Worst case', 'Side effects', 'Who is affected', 'Cost', 'Benefits', 'Timing', 'Reliability']
cr = D[D.nOpened > 0].groupby(['source', 'frame', 'ambiguity']).apply(
    lambda d: pd.Series({k: d.cards.str.split(';').apply(lambda s: k in s).mean() for k in cards})).reset_index()
cr.to_csv(os.path.join(out, 'card_rates.csv'), index=False); R['card_rates'] = cr.to_dict('records')
from firth import firth_logit
XH = ['int', 'loss', 'amb', 'loss_amb']
def effects_human(y, n):
    f = fit_ri_binomial(D[D.llm == 0], y, n, XH, 'unit')
    return f['beta'], f['V'], dict(sd=f['sd'], nobs=f['nobs'])
def effects_llm(d, y, n):
    d = d[d[n] > 0]
    Xm = np.column_stack([np.ones(len(d)), d.loss, d.amb, d.loss * d.amb])
    b, V = firth_logit(Xm, d[y].to_numpy(), d[n].to_numpy())
    return b, V
def ci(est, se, label):
    p = 2 * stats.norm.sf(abs(est / se))
    return dict(contrast=label, logOR=est, se=se, OR=np.exp(est), lo=np.exp(est - 1.96 * se), hi=np.exp(est + 1.96 * se), p=p)
cA = np.array([0, 1, 0, 1.]); cP = np.array([0, 1, 0, 0.]); cI = np.array([0, 0, 0, 1.])
def compare(y, n, llm_sources):
    bh, Vh, info = effects_human(y, n)
    d = D[D.source.isin(llm_sources)]
    bl, Vl = effects_llm(d, y, n)
    out = []
    for c, nm in [(cA, 'loss vs gain | ambiguous'), (cP, 'loss vs gain | precise'), (cI, 'Frame x Ambiguity')]:
        eh, sh = c @ bh, np.sqrt(c @ Vh @ c); el, sl = c @ bl, np.sqrt(c @ Vl @ c)
        out.append(ci(eh, sh, 'Human: ' + nm)); out.append(ci(el, sl, 'LLM: ' + nm))
        out.append(ci(eh - el, np.sqrt(sh ** 2 + sl ** 2), 'Human minus LLM: ' + nm))
    return dict(human_info=info, contrasts=out)
llms = sorted(Ld.source.unique())
R['threat_pooled_llm'] = compare('nThreat', 'nOpened', llms)
R['safe_pooled_llm'] = compare('safe', 'one', llms)
R['per_model'] = {m: dict(threat=compare('nThreat', 'nOpened', [m]), safe=compare('safe', 'one', [m])) for m in llms}
# Holm across the three per-model criterion-2 tests (threat)
ps = [(m, [c for c in R['per_model'][m]['threat']['contrasts'] if c['contrast'] == 'Human minus LLM: loss vs gain | ambiguous'][0]['p']) for m in llms]
order = sorted(ps, key=lambda t: t[1]); k = len(order); holm = {}; run = 0
for i, (m, p) in enumerate(order): run = max(run, min(1, (k - i) * p)); holm[m] = run
R['holm_threat_criterion2'] = holm
# simple robust check: per-source frame effect under ambiguity, Fisher/chi2 on pooled cards and choices
simp = []
for s, d in D.groupby('source'):
    a = d[d.amb == 1]
    for meas in ['threat', 'safe']:
        if meas == 'threat':
            g = a[(a.loss == 0) & (a.nOpened > 0)]; l = a[(a.loss == 1) & (a.nOpened > 0)]
            tab = [[g.nThreat.sum(), (g.nOpened - g.nThreat).sum()], [l.nThreat.sum(), (l.nOpened - l.nThreat).sum()]]
        else:
            g = a[a.loss == 0]; l = a[a.loss == 1]
            tab = [[g.safe.sum(), len(g) - g.safe.sum()], [l.safe.sum(), len(l) - l.safe.sum()]]
        orr, p = stats.fisher_exact(tab)
        simp.append(dict(source=s, measure=meas, gain_rate=tab[0][0] / max(sum(tab[0]), 1), loss_rate=tab[1][0] / max(sum(tab[1]), 1),
                         OR_gain_over_loss=orr, p_fisher=p))
R['fisher_ambiguous'] = simp
# chance comparison per source x cell
ch = []
for (s, fr, am), d in D[D.nOpened > 0].groupby(['source', 'frame', 'ambiguity']):
    k, n = int(d.nThreat.sum()), int(d.nOpened.sum())
    ch.append(dict(source=s, cell=f'{fr}/{am}', pooled=k / n, binom_p=stats.binomtest(k, n, 3 / 7).pvalue, n_cards=n))
R['chance'] = ch
json.dump(R, open(os.path.join(out, 'results_combined.json'), 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
print(json.dumps({k: R[k] for k in ['llm_total_records', 'llm_invalid', 'llm_retried', 'llm_over_limit', 'served_models']}, default=str))
print(desc.round(3).to_string())
def show(t, x):
    print('==', t)
    for c in x['contrasts']: print(f"  {c['contrast']}: OR={c['OR']:.3g} [{c['lo']:.3g},{c['hi']:.3g}] p={c['p']:.3g}")
show('THREAT pooled LLM', R['threat_pooled_llm']); show('SAFE pooled LLM', R['safe_pooled_llm'])
for m, x in R['per_model'].items(): show(m + ' threat', x['threat']); show(m + ' safe', x['safe'])
print('Holm', R['holm_threat_criterion2'])
print(pd.DataFrame(simp).round(4).to_string()); print(pd.DataFrame(ch).round(4).to_string())
