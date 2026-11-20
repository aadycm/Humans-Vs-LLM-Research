import json,math,os,sys
import numpy as np,pandas as pd
from scipy import stats
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.dirname(HERE)
sys.path.insert(0,HERE)
from firth import firth_logit
from glmm import fit_ri_binomial,contrast

OUT=os.path.join(ROOT,"results","followup")
os.makedirs(OUT,exist_ok=True)

MODELS=["gpt-4.1","gpt-4o","gpt-4o-mini","google/gemini-2.5-flash","qwen/qwen3-235b-a22b-2507","meta-llama/llama-4-maverick"]
SHORT={"gpt-4.1":"GPT-4.1","gpt-4o":"GPT-4o","gpt-4o-mini":"GPT-4o-mini","google/gemini-2.5-flash":"Gemini 2.5 Flash",
       "qwen/qwen3-235b-a22b-2507":"Qwen3 235B","meta-llama/llama-4-maverick":"Llama 4 Maverick"}
LEVELS=[0,2,3,4]
GAIN={"Q1","Q2","M3","M4"}   # gain worded side, everything else is loss worded
TOPIC={"Q1":"outbreak","M1":"outbreak","Q2":"fund","M2":"fund","Q3":"storm","M3":"storm","Q4":"wildfire","M4":"wildfire"}

# ---- load the llm runs ----
def load_llm():
    v2=[json.loads(l) for l in open(os.path.join(ROOT,"data","llm_runs_v2.jsonl"),encoding="utf-8")]
    main=[json.loads(l) for l in open(os.path.join(ROOT,"data","llm_runs.jsonl"),encoding="utf-8")]
    for r in main:
        r["wording"]="orig"; r["card_limit"]=4   # main study gpt runs are the orig wording 4 card cell
    d=pd.DataFrame(v2+main)
    dropped=int(d.over_limit.sum())
    d=d[~d.over_limit]   # the one gpt-4o run that listed all 7 cards on retry
    d["safe"]=(d.choice=="safe").astype(int)
    d["loss"]=(~d.scenario_id.isin(GAIN)).astype(int)
    d["set"]=np.where(d.scenario_id.str.startswith("M"),"mirrored","original")
    d["topic"]=d.scenario_id.map(TOPIC)
    return d,dropped

# ---- the rule fixed on nov 11 ----
def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return c-h,c+h

def gap_ci(kg,ng,kl,nl):
    # newcombe hybrid score interval for gain minus loss
    pg,pl=kg/ng,kl/nl; lg,ug=wilson(kg,ng); ll,ul=wilson(kl,nl)
    d=pg-pl
    return d,d-math.sqrt((pg-lg)**2+(ul-pl)**2),d+math.sqrt((ug-pg)**2+(pl-ll)**2)

def label(d,lo,hi):
    # round first so a gap of exactly 10 points isnt read as 9.999999 by float math
    d,lo,hi=round(d,9),round(lo,9),round(hi,9)
    if abs(d)>=0.10 and (lo>0 or hi<0): return "swayed"
    if lo>-0.10 and hi<0.10: return "within threshold"
    return "inconclusive"

def switch_point(labels):
    # smallest level that is within threshold and stays within it at every higher level
    for i,L in enumerate(LEVELS):
        if all(x=="within threshold" for x in labels[i:]): return L
    return None

def gap_row(sub,**keys):
    g=sub[sub.loss==0]; l=sub[sub.loss==1]
    d,lo,hi=gap_ci(g.safe.sum(),len(g),l.safe.sum(),len(l))
    return dict(**keys,n_gain=len(g),safe_gain=g.safe.sum(),n_loss=len(l),safe_loss=l.safe.sum(),
                pct_gain=100*g.safe.mean(),pct_loss=100*l.safe.mean(),gap=100*d,lo=100*lo,hi=100*hi,label=label(d,lo,hi))

def gap_table(d,filt=None,by_wording=False):
    rows=[]
    for m in MODELS:
        for L in LEVELS:
            s=d[(d.model==m)&(d.card_limit==L)]
            if filt is not None: s=s[filt(s)]
            if by_wording:
                for w in ["orig","p1","p2"]:
                    sw=s[s.wording==w]
                    if sw.loss.nunique()==2: rows.append(gap_row(sw,model=SHORT[m],cards=L,wording=w))
            else:
                rows.append(gap_row(s,model=SHORT[m],cards=L))
    return pd.DataFrame(rows)

def add_switch(t):
    sp={}
    for m,g in t.groupby("model",sort=False):
        L=switch_point(list(g.sort_values("cards").label)); sp[m]="no switch" if L is None else f"{L} cards"
    return sp

# ---- regression check: frame effect with topic and wording held fixed ----
def frame_model(d,m):
    # firth logit per model  safe ~ level + loss x level + topic + wording
    # topic is separable from wording because of the mirrored scenarios
    s=d[d.model==m].copy()
    cols=[]
    X=pd.DataFrame({"int":1.0},index=s.index)
    for L in LEVELS[1:]:
        X[f"L{L}"]=(s.card_limit==L).astype(float)
    for L in LEVELS:
        X[f"loss_L{L}"]=((s.card_limit==L)&(s.loss==1)).astype(float)
    for t in ["fund","storm","wildfire"]:
        X[f"topic_{t}"]=(s.topic==t).astype(float)
    for w in ["p1","p2"]:
        X[f"w_{w}"]=(s.wording==w).astype(float)
    b,V=firth_logit(X.to_numpy(),s.safe.to_numpy())
    names=list(X.columns); out={}
    for L in LEVELS:
        i=names.index(f"loss_L{L}"); se=math.sqrt(V[i,i])
        out[L]=dict(logOR=b[i],OR=math.exp(b[i]),lo=math.exp(b[i]-1.96*se),hi=math.exp(b[i]+1.96*se),p=2*stats.norm.sf(abs(b[i]/se)))
    # trend across 2 3 4 cards on the loss side  (the clean comparison since those share one prompt format)
    s2=s[(s.card_limit>=2)&(s.loss==1)]
    X2=np.column_stack([np.ones(len(s2)),s2.card_limit-3,
                        (s2.topic=="fund"),(s2.topic=="storm"),(s2.topic=="wildfire"),(s2.wording=="p1"),(s2.wording=="p2")]).astype(float)
    b2,V2=firth_logit(X2,s2.safe.to_numpy())
    se2=math.sqrt(V2[1,1])
    trend=dict(logOR_per_card=b2[1],OR_per_card=math.exp(b2[1]),lo=math.exp(b2[1]-1.96*se2),hi=math.exp(b2[1]+1.96*se2),p=2*stats.norm.sf(abs(b2[1]/se2)))
    return out,trend

# ---- people ----
def human_tables():
    # raw survey data lives in data/human which is gitignored (irb)
    h=pd.read_csv(os.path.join(ROOT,"data","human","combined_trials.csv"))
    h=h[h.source=="human"].copy()
    rows=[]
    for k in range(5):
        s=h[h.nOpened==k]; rows.append(gap_row(s,cards_opened=k))
    # also the plan's grouping 0-1 vs 2-3 vs 4 so groups are not tiny
    grp=lambda k:"0-1" if k<=1 else ("2-3" if k<=3 else "4")
    h["grp"]=h.nOpened.map(grp)
    rows2=[gap_row(h[h.grp==g],cards_opened=g) for g in ["0-1","2-3","4"]]
    # random intercept per person  safe ~ loss + few + loss x few + ambiguity
    h["few"]=(h.nOpened<=1).astype(float); h["loss_few"]=h.loss*h.few; h["n1"]=1
    f=fit_ri_binomial(h,"safe","n1",["int","loss","few","loss_few","amb"],"unit")
    c_many=contrast(f,[0,1,0,0,0],"loss effect, 2+ cards opened")
    c_few=contrast(f,[0,1,0,1,0],"loss effect, 0-1 cards opened")
    c_diff=contrast(f,[0,0,0,1,0],"difference (0-1 minus 2+)")
    # same model with gee  exchangeable correlation inside each person
    import statsmodels.api as sm,statsmodels.formula.api as smf
    g=smf.gee("safe ~ loss*few + amb",groups="unit",data=h,family=sm.families.Binomial(),cov_struct=sm.cov_struct.Exchangeable()).fit()
    b,se=g.params["loss:few"],g.bse["loss:few"]
    gee=dict(contrast="difference (0-1 minus 2+), gee exchangeable",OR=math.exp(b),lo=math.exp(b-1.96*se),hi=math.exp(b+1.96*se),p=float(g.pvalues["loss:few"]))
    # same gee without the exact vs range term  reported as a sensitivity check
    g2=smf.gee("safe ~ loss*few",groups="unit",data=h,family=sm.families.Binomial(),cov_struct=sm.cov_struct.Exchangeable()).fit()
    b,se=g2.params["loss:few"],g2.bse["loss:few"]
    gee["no_amb"]=dict(OR=math.exp(b),lo=math.exp(b-1.96*se),hi=math.exp(b+1.96*se),p=float(g2.pvalues["loss:few"]))
    return pd.DataFrame(rows),pd.DataFrame(rows2),dict(person_sd=f["sd"],n_decisions=f["nobs"],n_people=f["ngroups"],tests=[c_few,c_many,c_diff],gee=gee)


# ---- bootstrap check on the labels ----
def boot_labels(d,filt,B=4000,seed=1):
    # resample runs inside each gain and loss cell  percentile interval  same rule
    rng=np.random.default_rng(seed); rows=[]
    for m in MODELS:
        for L in LEVELS:
            s=d[(d.model==m)&(d.card_limit==L)]; s=s[filt(s)]
            g=s[s.loss==0].safe.to_numpy(); l=s[s.loss==1].safe.to_numpy()
            bg=rng.binomial(len(g),g.mean(),B)/len(g); bl=rng.binomial(len(l),l.mean(),B)/len(l)
            diff=bg-bl; lo,hi=np.percentile(diff,[2.5,97.5])
            rows.append(dict(model=SHORT[m],cards=L,gap=100*(g.mean()-l.mean()),boot_lo=100*lo,boot_hi=100*hi,boot_label=label(g.mean()-l.mean(),lo,hi)))
    return pd.DataFrame(rows)

def human_boot(B=2000,seed=2):
    # resample people  keep all four of a persons decisions together
    h=pd.read_csv(os.path.join(ROOT,"data","human","combined_trials.csv")); h=h[h.source=="human"].copy()
    h["grp"]=h.nOpened.map(lambda k:"0-1" if k<=1 else ("2-3" if k<=3 else "4"))
    ids=h.unit.unique(); by={u:x for u,x in h.groupby("unit")}; rng=np.random.default_rng(seed)
    out={g:[] for g in ["0-1","2-3","4"]}
    for _ in range(B):
        hb=pd.concat([by[u] for u in rng.choice(ids,len(ids))])
        for g in out:
            x=hb[hb.grp==g]; a=x[x.loss==0].safe; b=x[x.loss==1].safe
            if len(a) and len(b): out[g].append(a.mean()-b.mean())
    rows=[]
    for g,v in out.items():
        x=h[h.grp==g]; d0=x[x.loss==0].safe.mean()-x[x.loss==1].safe.mean(); lo,hi=np.percentile(v,[2.5,97.5])
        rows.append(dict(cards_opened=g,gap=100*d0,boot_lo=100*lo,boot_hi=100*hi,boot_label=label(d0,lo,hi)))
    return pd.DataFrame(rows)

def card_choices(d):
    # which cards the models picked  share of runs that opened each card  split by frame
    s=d[d.card_limit>0]; rows=[]
    for (m,L,fr),g in s.groupby(["model","card_limit","loss"]):
        cnt={}
        for cs in g.cards_opened:
            for c in cs: cnt[c]=cnt.get(c,0)+1
        for c,k in cnt.items(): rows.append(dict(model=SHORT[m],card_limit=L,frame="loss" if fr else "gain",card=c,share=100*k/len(g),n_runs=len(g)))
    return pd.DataFrame(rows)

def batch_check(d):
    # gpt q1-q4 original wording at 4 cards came from the oct 31 batch  compare with the nov paraphrase runs of the same scenarios
    rows=[]
    for m in ["gpt-4.1","gpt-4o","gpt-4o-mini"]:
        s=d[(d.model==m)&(d.card_limit==4)&(d.set=="original")]
        for lab,x in [("oct 31 batch (orig wording)",s[s.wording=="orig"]),("nov batch (p1+p2)",s[s.wording!="orig"])]:
            rows.append(dict(model=SHORT[m],batch=lab,n=len(x),safe_gain=100*x[x.loss==0].safe.mean(),safe_loss=100*x[x.loss==1].safe.mean()))
    return pd.DataFrame(rows)

def main():
    d,dropped=load_llm()
    res={"runs_used":int(len(d)),"runs_dropped":dropped}
    allt=gap_table(d); orig=gap_table(d,lambda s:s.set=="original"); mir=gap_table(d,lambda s:s.set=="mirrored")
    # balanced view  original wording only so every topic counts once per frame  q1-q4 vs m1-m4  120 per side
    bal=gap_table(d,lambda s:s.wording=="orig")
    origw=gap_table(d,lambda s:(s.set=="original")&(s.wording=="orig"))   # the two halves of the balanced view
    bal.to_csv(os.path.join(OUT,"gap_balanced.csv"),index=False); origw.to_csv(os.path.join(OUT,"gap_originals_origwording.csv"),index=False)
    res["switch_balanced"]=add_switch(bal)
    # how many cards the models actually opened at each limit
    cards=d[d.card_limit>0].groupby(["model","card_limit"]).n_cards_opened.mean().unstack().round(3)
    cards.to_csv(os.path.join(OUT,"cards_opened_by_limit.csv"))
    word=gap_table(d,lambda s:s.set=="original",by_wording=True)
    allt.to_csv(os.path.join(OUT,"gap_all.csv"),index=False); orig.to_csv(os.path.join(OUT,"gap_originals.csv"),index=False)
    mir.to_csv(os.path.join(OUT,"gap_mirrored.csv"),index=False); word.to_csv(os.path.join(OUT,"gap_by_wording.csv"),index=False)
    res["switch_all"]=add_switch(allt); res["switch_originals"]=add_switch(orig); res["switch_mirrored"]=add_switch(mir)
    # paraphrase spread  biggest minus smallest gap across the 3 versions in each cell
    sp=word.groupby(["model","cards"]).gap.agg(lambda x:x.max()-x.min()).reset_index(name="spread")
    sp.to_csv(os.path.join(OUT,"paraphrase_spread.csv"),index=False)
    reg={}
    for m in MODELS:
        out,trend=frame_model(d,m); reg[SHORT[m]]=dict(by_level={str(k):v for k,v in out.items()},trend_loss_2to4=trend)
    res["regression"]=reg
    hall,hgrp,hglmm=human_tables()
    hall.to_csv(os.path.join(OUT,"human_gap_by_cards.csv"),index=False); hgrp.to_csv(os.path.join(OUT,"human_gap_grouped.csv"),index=False)
    res["human_glmm"]=hglmm
    bb=boot_labels(d,lambda s:s.wording=="orig"); bp=boot_labels(d,lambda s:s.wording.notna(),seed=3)
    bb["newcombe_label"]=bal.label.values; bp["newcombe_label"]=allt.label.values
    bb.to_csv(os.path.join(OUT,"boot_balanced.csv"),index=False); bp.to_csv(os.path.join(OUT,"boot_pooled.csv"),index=False)
    res["boot_agree"]=dict(balanced=int((bb.boot_label==bb.newcombe_label).sum()),pooled=int((bp.boot_label==bp.newcombe_label).sum()),of=len(bb))
    hb=human_boot(); hb["newcombe_label"]=hgrp.label.values; hb.to_csv(os.path.join(OUT,"human_boot.csv"),index=False)
    card_choices(d).to_csv(os.path.join(OUT,"card_choices.csv"),index=False)
    batch_check(d).to_csv(os.path.join(OUT,"batch_check.csv"),index=False)
    json.dump(res,open(os.path.join(OUT,"followup_results.json"),"w"),indent=1,default=float)
    pd.set_option("display.width",200); pd.set_option("display.max_rows",200)
    fmt=lambda t:t.round(1).to_string(index=False)
    print("runs used",len(d),"dropped",dropped)
    print("\n== balanced (original wording, q vs m)\n"+fmt(bal[["model","cards","n_gain","n_loss","pct_gain","pct_loss","gap","lo","hi","label"]])); print(res["switch_balanced"])
    print("\n== all scenarios (the rule)\n"+fmt(allt[["model","cards","pct_gain","pct_loss","gap","lo","hi","label"]]))
    print("switch points:",res["switch_all"])
    print("\n== originals only\n"+fmt(orig[["model","cards","gap","lo","hi","label"]])); print(res["switch_originals"])
    print("\n== mirrored only\n"+fmt(mir[["model","cards","gap","lo","hi","label"]])); print(res["switch_mirrored"])
    print("\n== paraphrase spread (points)\n"+sp.pivot(index="model",columns="cards",values="spread").round(0).to_string())
    print("\n== regression  frame odds ratio by level (safe odds under loss vs gain  topic and wording held fixed)")
    for m,v in reg.items():
        print(f"  {m:17}"+"  ".join(f"L{L} OR {v['by_level'][str(L)]['OR']:.3f} [{v['by_level'][str(L)]['lo']:.3f},{v['by_level'][str(L)]['hi']:.3f}]" for L in LEVELS)
              +f"   trend 2-4 cards loss side: OR/card {v['trend_loss_2to4']['OR_per_card']:.2f} p={v['trend_loss_2to4']['p']:.3g}")
    print("\n== people by cards opened\n"+fmt(hall[["cards_opened","n_gain","n_loss","pct_gain","pct_loss","gap","lo","hi","label"]]))
    print(fmt(hgrp[["cards_opened","n_gain","n_loss","pct_gain","pct_loss","gap","lo","hi","label"]]))
    for t in hglmm["tests"]: print(f"  {t['contrast']:32} OR {t['OR']:.2f} [{t['lo']:.2f},{t['hi']:.2f}] p={t['p']:.3g}")
    print("  person sd",round(hglmm["person_sd"],2))

if __name__=="__main__":
    main()
