import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from glmm import fit_ri_binomial, contrast
from scipy import stats
import statsmodels.api as sm, statsmodels.formula.api as smf
import os
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=os.path.join(ROOT,'data','human')+os.sep  # NOT in repo: raw human data stays on Penn State storage (IRB)
w=pd.read_csv(R+'aadithya_data.csv',encoding='utf-8-sig'); L=pd.read_csv(R+'aadithya_long.csv',encoding='utf-8-sig')
out={}
med=w['Duration (in seconds)'].median(); cut=med/3
spd=w['Duration (in seconds)']<cut
out['n_received']=len(w); out['median_dur']=med; out['speed_cut']=cut; out['n_speeders']=int(spd.sum())
keep=set(w.loc[~spd,'ResponseId']); w=w[~spd]; L=L[L.ResponseId.isin(keep)].copy()
out['n_final']=len(w)
L['loss']=(L.frame=='loss').astype(int); L['amb']=(L.ambiguity=='ambiguous').astype(int)
L['int']=1; L['loss_amb']=L.loss*L.amb
# cell means coded so gain/loss in both ambiguity levels
X=['int','loss','amb','loss_amb']
desc=L.groupby(['frame','ambiguity']).apply(lambda d: pd.Series(dict(
  n=len(d), zero=(d.nOpened==0).mean(), nOpened=d.nOpened.mean(),
  pooled_threat=d.nThreat.sum()/d.nOpened.sum(), mean_threat=d.threatShare.mean(),
  n_with_cards=(d.nOpened>0).sum(), safe=(d.choice=='safe').mean(), risky=d.risky.mean(),
  ms_med=d.ms.median()/1000)))
print(desc); out['desc']=desc.reset_index().to_dict('records')
# primary binomial GLMM
f=fit_ri_binomial(L,'nThreat','nOpened',X,'ResponseId')
print('GLMM threat', f['beta'], f['sd'], f['nobs'], f['ngroups'], f['ok'])
cs=[contrast(f,[0,1,0,1],'Loss vs gain | ambiguous (H1 criterion 1)'),
    contrast(f,[0,1,0,0],'Loss vs gain | precise'),
    contrast(f,[0,0,0,1],'Frame x Ambiguity interaction'),
    contrast(f,[0,0,1,0],'Ambiguous vs precise | gain'),
    contrast(f,[0,0,1,1],'Ambiguous vs precise | loss')]
# cell predicted probs at random effect 0
inv=lambda x:1/(1+np.exp(-x))
cells={'gain/precise':[1,0,0,0],'gain/ambiguous':[1,0,1,0],'loss/precise':[1,1,0,0],'loss/ambiguous':[1,1,1,1]}
cellp={k:dict(p=inv(np.dot(v,f['beta'])), lo=inv(np.dot(v,f['beta'])-1.96*np.sqrt(np.array(v)@f['V']@np.array(v))), hi=inv(np.dot(v,f['beta'])+1.96*np.sqrt(np.array(v)@f['V']@np.array(v)))) for k,v in cells.items()}
out['threat_glmm']=dict(contrasts=cs, sd=f['sd'], nobs=f['nobs'], ngroups=f['ngroups'], cells=cellp)
for c in cs: print(c)
print(cellp)
# chance comparisons: one-sample vs 3/7 per cell (binomial GLMM intercept-only per cell -> use GEE-ish simple: cluster not needed, one trial per person per cell)
ch=[]
for (fr,am),d in L[L.nOpened>0].groupby(['frame','ambiguity']):
    k=d.nThreat.sum(); n=d.nOpened.sum()
    # person-level mean threat share vs 3/7 (t-test), robust to clustering of cards within person
    t=stats.ttest_1samp(d.threatShare,3/7)
    ch.append(dict(cell=f'{fr}/{am}', n_people=len(d), mean=d.threatShare.mean(), pooled=k/n, t=t.statistic, df=len(d)-1, p=t.pvalue))
    print(ch[-1])
out['chance']=ch
# secondary: safe choice logistic GLMM
L['safe']=(L.choice=='safe').astype(int); L['one']=1
f2=fit_ri_binomial(L,'safe','one',X,'ResponseId')
print('GLMM safe', f2['beta'], f2['sd'], f2['ok'])
cs2=[contrast(f2,[0,1,0,1],'Loss vs gain | ambiguous (safe choice)'),
     contrast(f2,[0,1,0,0],'Loss vs gain | precise (manipulation check)'),
     contrast(f2,[0,1,0,0.5],'Loss vs gain | averaged over ambiguity'),
     contrast(f2,[0,0,0,1],'Frame x Ambiguity interaction'),
     contrast(f2,[0,0,1,0],'Ambiguous vs precise | gain'),
     contrast(f2,[0,0,1,1],'Ambiguous vs precise | loss')]
for c in cs2: print(c)
out['safe_glmm']=dict(contrasts=cs2, sd=f2['sd'])
# robustness (c): LMM on threatShare, GEE binomial
Lc=L[L.nOpened>0].copy()
lmm=smf.mixedlm('threatShare ~ loss*amb', Lc, groups=Lc.ResponseId).fit(reml=True)
b=lmm.params; V=lmm.cov_params()
c=pd.Series(0.0,index=b.index); c['loss']=1; c['loss:amb']=1
est=c@b; se=np.sqrt(c@V@c)
out['robust_lmm']=dict(est=est, lo=est-1.96*se, hi=est+1.96*se, p=2*stats.norm.sf(abs(est/se)), inter=b['loss:amb'], inter_p=lmm.pvalues['loss:amb'])
print('LMM', out['robust_lmm'])
Lc['nonthreat']=Lc.nOpened-Lc.nThreat
gee=smf.gee('nThreat ~ loss*amb', groups='ResponseId', data=Lc, family=sm.families.Binomial(), exposure=None,
            cov_struct=sm.cov_struct.Exchangeable(), freq_weights=None) 
# binomial with trials: use endog as proportion with var_weights
gee=sm.GEE.from_formula('threatShare ~ loss*amb', groups='ResponseId', data=Lc, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable(), weights=Lc.nOpened)
gr=gee.fit(); b=gr.params; V=gr.cov_params()
c=pd.Series(0.0,index=b.index); c['loss']=1; c['loss:amb']=1
est=c@b; se=np.sqrt(c@V@c)
out['robust_gee']=dict(OR=np.exp(est), lo=np.exp(est-1.96*se), hi=np.exp(est+1.96*se), p=2*stats.norm.sf(abs(est/se)))
print('GEE', out['robust_gee'])
# number of cards opened & zero-card (descriptive + Poisson? use LMM on nOpened)
lmm2=smf.mixedlm('nOpened ~ loss*amb', L, groups=L.ResponseId).fit()
out['nopened_lmm']=dict(params=lmm2.params.to_dict(), p=lmm2.pvalues.to_dict())
print(lmm2.summary())
# decision time
L['logms']=np.log(L.ms/1000)
lmm3=smf.mixedlm('logms ~ loss*amb', L, groups=L.ResponseId).fit()
out['time_lmm']=dict(params=lmm3.params.to_dict(), p=lmm3.pvalues.to_dict())
print(lmm3.summary())
# order/scenario: zero-card by scenario
print(L.groupby('scenario').agg(zero=('nOpened',lambda x:(x==0).mean()), nOpened=('nOpened','mean')))
# self-report Q17 vs threat share in ambiguous scenarios
amb=L[(L.amb==1)&(L.nOpened>0)].groupby('ResponseId').threatShare.mean()
q=w.set_index('ResponseId').Q17
j=pd.concat([amb,q],axis=1,join='inner').dropna()
r=stats.spearmanr(j.threatShare,j.Q17); out['q17']=dict(rho=r.statistic,p=r.pvalue,n=len(j))
print('Q17',out['q17'], w.Q17.describe())
# worst-case card opened in ambiguous & choice
L['wc']=L.cardsOpened.fillna('').str.contains('Worst case').astype(int)
Lw=L[L.nOpened>0]
ct=pd.crosstab(Lw.wc,Lw.choice); print(ct)
f4=fit_ri_binomial(Lw.assign(wc=Lw.wc),'safe','one',['int','wc','loss','amb'],'ResponseId')
out['wc_safe']=contrast(f4,[0,1,0,0],'Opened Worst-case card -> safe choice'); print(out['wc_safe'])
# card open rates by condition (among trials with >=1 card)
cards=['Worst case','Side effects','Who is affected','Cost','Benefits','Timing','Reliability']
rates=Lw.groupby(['frame','ambiguity']).apply(lambda d: pd.Series({k: d.cardsOpened.fillna('').str.split(';').apply(lambda s:k in s).mean() for k in cards}))
print(rates.round(3)); out['card_rates']=rates.reset_index().to_dict('records')
# risk course moderator on threat share
Lm=L.copy(); Lm['course']=(Lm.QID14==1).astype(int); Lm['course_loss']=Lm.course*Lm.loss
f5=fit_ri_binomial(Lm,'nThreat','nOpened',['int','loss','amb','loss_amb','course','course_loss'],'ResponseId')
out['course']=[contrast(f5,[0,0,0,0,1,0],'Risk course (main, gain)'),contrast(f5,[0,0,0,0,0,1],'Risk course x loss frame')]
print(out['course'])
# demographics
out['demo']={c:w[c].value_counts().sort_index().to_dict() for c in ['QID12','QID13','QID14','QID15','Q17']}
out['q17_mean']=w.Q17.mean(); out['q17_sd']=w.Q17.std()
out['dates']=[w.StartDate.min(),w.StartDate.max()]
out['dur_med_final']=w['Duration (in seconds)'].median()
L.to_csv(os.path.join(R,'analysis_long.csv'),index=False)
json.dump(out,open(os.path.join(ROOT,'results','human','results_human.json'),'w'),default=lambda o: o.item() if hasattr(o,'item') else str(o),indent=1)
