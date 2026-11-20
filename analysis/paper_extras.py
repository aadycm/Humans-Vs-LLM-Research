import os,sys,json
import numpy as np,pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import analyze_followup as a

# extra numbers in the paper that analyze_followup.py doesnt write out
# run analyze_followup.py first since this reads its csv files
RES=os.path.join(a.ROOT,"results","followup")
OUT=os.path.join(RES,"paper_extras.json")
ORDER=["GPT-4.1","GPT-4o","Qwen3 235B","Gemini 2.5 Flash","Llama 4 Maverick","GPT-4o-mini"]
NAMES={"gpt-4.1":"GPT-4.1","gpt-4o":"GPT-4o","gpt-4o-mini":"GPT-4o-mini","google/gemini-2.5-flash":"Gemini 2.5 Flash",
       "qwen/qwen3-235b-a22b-2507":"Qwen3 235B","meta-llama/llama-4-maverick":"Llama 4 Maverick"}
GAIN=set(a.GAIN)

def gap(x):
    return (x[x.loss==0].safe.mean()-x[x.loss==1].safe.mean())*100

def change_2_to_4(b,m,B=4000,seed=7):
    # change in the balanced gap from 2 to 4 cards
    # resample runs inside each scenario so every topic keeps its weight
    rng=np.random.default_rng(seed)
    x2=b[(b.M==m)&(b.card_limit==2)];x4=b[(b.M==m)&(b.card_limit==4)]
    c2=[(s,g.safe.values) for s,g in x2.groupby("scenario_id")]
    c4=[(s,g.safe.values) for s,g in x4.groupby("scenario_id")]
    def g_of(cells):
        gs=np.concatenate([v for s,v in cells if s in GAIN]);ls=np.concatenate([v for s,v in cells if s not in GAIN])
        return (gs.mean()-ls.mean())*100
    bs=[]
    for _ in range(B):
        r2=[(s,rng.choice(v,len(v))) for s,v in c2];r4=[(s,rng.choice(v,len(v))) for s,v in c4]
        bs.append(g_of(r4)-g_of(r2))
    lo,hi=np.percentile(bs,[2.5,97.5])
    return dict(change=gap(x4)-gap(x2),lo=lo,hi=hi)

def main():
    d,_=a.load_llm()
    d["M"]=d.model.map(lambda x:NAMES.get(x,x))
    b=d[d.wording=="orig"]
    R={}
    # section 4.3 the gap change from 2 to 4 cards
    R["change_2_to_4"]={m:change_2_to_4(b,m) for m in ORDER}
    # limitations how many balanced cells sit fully inside other margins
    bal=pd.read_csv(os.path.join(RES,"gap_balanced.csv"))
    R["cells_within_margin"]={str(k):int(((bal.lo>-k)&(bal.hi<k)).sum()) for k in (5,10,15)}
    # discussion how many card gaps are below that models no card gap
    below=0
    for m in bal.model.unique():
        z=bal[bal.model==m].set_index("cards").gap
        below+=sum(z[k]<z[0] for k in (2,3,4))
    R["card_gaps_below_no_card"]=int(below)
    # section 4.4 gap without the outbreak topic q1 and m1
    R["gap_without_outbreak"]={m:{str(L):gap(b[(b.M==m)&(b.card_limit==L)&(~b.scenario_id.isin(["Q1","M1"]))]) for L in (2,3,4)} for m in ("GPT-4.1","GPT-4o")}
    # table s5 safe choices by scenario with cards
    t=b[b.card_limit>0].groupby(["M","scenario_id"]).safe.agg(["sum","count"])
    R["table_s5"]={m:{s:f"{int(t.loc[(m,s),'sum'])}/{int(t.loc[(m,s),'count'])}" for s in ("Q1","Q2","M3","M4","Q3","Q4","M1","M2")} for m in ORDER}
    # section 3.4 how many runs with cards needed a retry
    c=d[d.card_limit>0]
    R["retries"]={NAMES.get(k,k):int(v) for k,v in c.groupby("model").retried.sum().items()}
    R["runs_with_cards"]=int(len(c))
    with open(OUT,"w") as f:
        json.dump(R,f,indent=1,default=float)
    print("saved",OUT)
    for m,v in R["change_2_to_4"].items():
        print(f"  {m}: {v['change']:+.1f} ({v['lo']:+.1f} to {v['hi']:+.1f})")

if __name__=="__main__":
    main()
