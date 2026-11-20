import os, json, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R=json.load(open(os.path.join(ROOT,'results','human','results_human.json'))); L=pd.read_csv(os.path.join(ROOT,'data','human','analysis_long.csv'))
os.makedirs(os.path.join(ROOT,'figures','main_study'),exist_ok=True); os.chdir(os.path.join(ROOT,'figures','main_study'))
B,O='#2a78d6','#eb6834'; INK='#0b0b0b'; MUT='#52514e'; GRID='#e4e3df'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.edgecolor':MUT,'axes.labelcolor':INK,'xtick.color':MUT,'ytick.color':MUT,'axes.spines.top':False,'axes.spines.right':False})
def style(ax):
    ax.yaxis.grid(True,color=GRID,lw=0.8); ax.set_axisbelow(True)
amb=['precise','ambiguous']; x=np.arange(2); wdt=0.34
# Fig 1
fig,ax=plt.subplots(figsize=(6.2,3.4)); style(ax)
c=R['threat_glmm']['cells']
for i,(fr,col) in enumerate([('gain',B),('loss',O)]):
    p=[c[f'{fr}/{a}']['p']*100 for a in amb]; lo=[c[f'{fr}/{a}']['lo']*100 for a in amb]; hi=[c[f'{fr}/{a}']['hi']*100 for a in amb]
    xs=x+(i-0.5)*(wdt+0.02)
    ax.bar(xs,p,wdt,color=col,label=f'{fr.capitalize()} frame')
    ax.errorbar(xs,p,yerr=[np.subtract(p,lo),np.subtract(hi,p)],fmt='none',ecolor=INK,capsize=4,lw=1.2)
    for xx,pp in zip(xs,p): ax.text(xx,4,f'{pp:.0f}%',ha='center',color='white',fontsize=9,fontweight='bold')
ax.axhline(300/7,ls='--',color=MUT,lw=1.2,label='Chance (3 of 7 = 43%)')
ax.set_xticks(x,['Precise odds','Ambiguous odds']); ax.set_ylim(0,70); ax.set_ylabel('Threat cards, % of cards opened')
ax.legend(frameon=False,loc='upper left',ncol=3,fontsize=9); fig.tight_layout(); fig.savefig('fig1_threat_share.png',dpi=220)
# Fig 2
fig,ax=plt.subplots(figsize=(6.2,3.4)); style(ax)
for i,(fr,col) in enumerate([('gain',B),('loss',O)]):
    ps=[];los=[];his=[]
    for a in amb:
        d=L[(L.frame==fr)&(L.ambiguity==a)]; k=d.safe.sum(); n=len(d)
        lo,hi=proportion_confint(k,n,method='wilson'); ps.append(k/n*100); los.append(lo*100); his.append(hi*100)
    xs=x+(i-0.5)*(wdt+0.02)
    ax.bar(xs,ps,wdt,color=col,label=f'{fr.capitalize()} frame')
    ax.errorbar(xs,ps,yerr=[np.subtract(ps,los),np.subtract(his,ps)],fmt='none',ecolor=INK,capsize=4,lw=1.2)
    for xx,pp in zip(xs,ps): ax.text(xx,4,f'{pp:.0f}%',ha='center',color='white',fontsize=9,fontweight='bold')
ax.axhline(50,ls='--',color=MUT,lw=1.2,label='50%')
ax.set_xticks(x,['Precise odds','Ambiguous odds']); ax.set_ylim(0,90); ax.set_ylabel('Chose the safe option, %')
ax.legend(frameon=False,loc='upper left',ncol=2); fig.tight_layout(); fig.savefig('fig2_safe_choice.png',dpi=220)
# Fig 3 small multiples by position
g=L.groupby('scenario').agg(zero=('nOpened',lambda s:(s==0).mean()*100),ms=('ms',lambda s:s.median()/1000))
labs=['1\nGain·precise','2\nGain·ambig.','3\nLoss·precise','4\nLoss·ambig.']
fig,axs=plt.subplots(1,2,figsize=(6.6,3.0))
for ax,col,ttl,fmt in [(axs[0],'zero','Opened no cards (%)','{:.0f}%'),(axs[1],'ms','Median decision time (s)','{:.0f}s')]:
    style(ax); ax.plot(range(1,5),g[col],color=B,lw=2,marker='o',ms=7,markeredgecolor='white',markeredgewidth=2)
    for i,v in enumerate(g[col]): ax.text(i+1,v+(2 if col=='zero' else 2),fmt.format(v),ha='center',fontsize=8.5,color=INK)
    ax.set_xticks(range(1,5),labs,fontsize=7.5); ax.set_title(ttl,fontsize=10,color=INK,loc='left'); ax.set_ylim(0,max(g[col])*1.25); ax.set_xlim(0.6,4.4)
fig.text(0.5,0.01,'Scenario position (fixed order)',ha='center',fontsize=9,color=MUT)
fig.tight_layout(rect=(0,0.04,1,1)); fig.savefig('fig3_engagement_by_position.png',dpi=220)
