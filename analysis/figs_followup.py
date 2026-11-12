import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

HERE=os.path.dirname(os.path.abspath(__file__))
RES=os.path.join(os.path.dirname(HERE),"results","followup")
FIG=os.path.join(os.path.dirname(HERE),"figures")
os.makedirs(FIG,exist_ok=True)

# colors from the dataviz reference palette  blue and orange passed the colorblind check
BLUE,ORANGE="#2a78d6","#eb6834"
INK,INK2,MUTED,GRID,ZONE,BG="#1f1f1d","#52514e","#8a8984","#e6e5e1","#f1f0ec","#ffffff"
ORDER=["GPT-4.1","GPT-4o","Qwen3 235B","Gemini 2.5 Flash","Llama 4 Maverick","GPT-4o-mini"]
LEVELS=[0,2,3,4]

plt.rcParams.update({
    "font.family":"Inter","font.size":9.5,"axes.titlesize":11,"axes.edgecolor":GRID,"axes.linewidth":0.8,
    "axes.labelcolor":INK2,"xtick.color":INK2,"ytick.color":INK2,"xtick.major.size":0,"ytick.major.size":0,
    "axes.facecolor":BG,"figure.facecolor":BG,"savefig.facecolor":BG,"legend.frameon":False})

def save(fig,name):
    for ext in ["png","pdf"]:
        fig.savefig(os.path.join(FIG,f"{name}.{ext}"),dpi=300 if ext=="png" else None,bbox_inches="tight",pad_inches=0.15)
    plt.close(fig)

def base(ax,xs,ylo,yhi,zone_label=False):
    ax.axhspan(-10,10,color=ZONE,lw=0,zorder=0)   # within 10 points  the not swayed zone from the rule
    ax.axhline(0,color="#d6d5d0",lw=0.8,zorder=1)
    if zone_label: ax.text(xs[-1]+0.25,0,"within\n±10 pts",fontsize=7.5,color=MUTED,va="center",ha="left")
    ax.set_xticks(xs); ax.set_ylim(ylo,yhi); ax.set_yticks(range(0,yhi,20) if yhi>0 else [])
    ax.set_xlim(xs[0]-0.4,xs[-1]+0.4)
    for s in ["top","right","left"]: ax.spines[s].set_visible(False)
    ax.grid(axis="y",color=GRID,lw=0.6); ax.set_axisbelow(True)

def series(ax,x,y,lo,hi,labels,color,ms=7):
    x,y,lo,hi=list(x),list(y),list(lo),list(hi)
    ax.fill_between(x,lo,hi,color=color,alpha=0.14,lw=0,zorder=2)   # 95% ci ribbon
    ax.plot(x,y,color=color,lw=2,zorder=3,solid_capstyle="round")
    for xi,yi,lab in zip(x,y,labels):
        if lab=="swayed": ax.plot(xi,yi,"o",ms=ms,color=color,mec=BG,mew=1.5,zorder=4)
        elif lab=="not swayed": ax.plot(xi,yi,"o",ms=ms,mfc=BG,mec=color,mew=2,zorder=4)
        else: ax.plot(xi,yi,"D",ms=ms-1.5,mfc=BG,mec=color,mew=2,zorder=4)

def legend_handles(color=INK2):
    return [Line2D([],[],marker="o",ls="",ms=7,color=color,mec=BG,label="Swayed"),
            Line2D([],[],marker="o",ls="",ms=7,mfc=BG,mec=color,mew=2,label="Not swayed"),
            Line2D([],[],marker="D",ls="",ms=5.5,mfc=BG,mec=color,mew=2,label="Inconclusive"),
            Patch(color=ZONE,label="Gap within ±10 points")]

def switch_text(g):
    labs=list(g.sort_values("cards").label); cards=list(g.sort_values("cards").cards)
    for i,L in enumerate(cards):
        if all(x=="not swayed" for x in labs[i:]): return f"Stops being swayed at {L} cards"
    if all(x=="swayed" for x in labs): return "Swayed at every card level"
    return "No clear switch point"

# fig 1  the main result  one panel per model
def fig_models():
    t=pd.read_csv(os.path.join(RES,"gap_all.csv"))
    fig,axs=plt.subplots(2,3,figsize=(10,6.2),sharex=True,sharey=True)
    for i,(ax,m) in enumerate(zip(axs.ravel(),ORDER)):
        g=t[t.model==m].sort_values("cards")
        base(ax,LEVELS,-15,100)
        series(ax,g.cards,g.gap,g.lo,g.hi,g.label,BLUE)
        # label the first and last point so the drop is readable without the axis
        for x,y in [(g.cards.iloc[0],g.gap.iloc[0]),(g.cards.iloc[-1],g.gap.iloc[-1])]:
            ax.annotate(f"{y:.0f}",(x,y),xytext=(0,9),textcoords="offset points",ha="center",fontsize=8.5,color=INK,fontweight="semibold")
        ax.set_title(m,loc="left",color=INK,fontweight="semibold",pad=18)
        ax.text(0,1.035,switch_text(g),transform=ax.transAxes,fontsize=8.5,color=INK2)
    for ax in axs[:,0]: ax.set_ylabel("Wording gap (percentage points)")
    for ax in axs[1]: ax.set_xlabel("Cards the model could open")
    fig.legend(handles=legend_handles(),loc="lower center",ncol=4,fontsize=9,bbox_to_anchor=(0.5,-0.04),labelcolor=INK)
    fig.text(0.0,1.04,"How much gain vs loss wording changes each model's choice",fontsize=13,fontweight="semibold",color=INK)
    fig.text(0.0,1.005,"Gap = % picking the safe option under gain wording minus % under loss wording. 240 runs per side per point. Shaded band = 95% CI.",fontsize=8.8,color=INK2)
    fig.tight_layout(h_pad=2.2)
    save(fig,"fig1_models_gap")

# fig 2  people  grouped so each point has enough decisions
def fig_people():
    g=pd.read_csv(os.path.join(RES,"human_gap_grouped.csv"))
    one=pd.read_csv(os.path.join(RES,"human_gap_by_cards.csv"))
    fig,ax=plt.subplots(figsize=(5.2,3.9))
    xs=[0,1,2]
    base(ax,xs,-25,60)
    ax.set_yticks([-20,0,20,40])
    series(ax,xs,g.gap,g.lo,g.hi,g.label,ORANGE,ms=8)
    for x,(_,r) in zip(xs,g.iterrows()):
        ax.annotate(f"{r.gap:+.0f}".replace("-","\u2212"),(x,r.gap),xytext=(13,-3),textcoords="offset points",fontsize=8.5,color=INK,fontweight="semibold")
    ax.set_xticks(xs); ax.set_xticklabels([f"0–1 cards\n(n = {g.n_gain[0]+g.n_loss[0]})",f"2–3 cards\n(n = {g.n_gain[1]+g.n_loss[1]})",f"4 cards\n(n = {g.n_gain[2]+g.n_loss[2]})"])
    ax.set_ylabel("Wording gap (percentage points)")
    ax.set_title("People: wording gap by cards they chose to open",loc="left",color=INK,fontweight="semibold",pad=22)
    ax.text(0,1.035,"198 people, 792 decisions. Shaded band = 95% CI.",transform=ax.transAxes,fontsize=8.5,color=INK2)
    ax.legend(handles=legend_handles(),loc="upper right",fontsize=8,labelcolor=INK)
    fig.tight_layout()
    save(fig,"fig2_people_gap")

# fig 3  original vs mirrored scenarios
def fig_sets():
    o=pd.read_csv(os.path.join(RES,"gap_originals.csv")); mi=pd.read_csv(os.path.join(RES,"gap_mirrored.csv"))
    fig,axs=plt.subplots(2,3,figsize=(10,6.2),sharex=True,sharey=True)
    for ax,m in zip(axs.ravel(),ORDER):
        base(ax,LEVELS,-15,100)
        for t,c in [(o,BLUE),(mi,ORANGE)]:
            g=t[t.model==m].sort_values("cards")
            series(ax,g.cards,g.gap,g.lo,g.hi,g.label,c,ms=6)
        ax.set_title(m,loc="left",color=INK,fontweight="semibold")
    for ax in axs[:,0]: ax.set_ylabel("Wording gap (percentage points)")
    for ax in axs[1]: ax.set_xlabel("Cards the model could open")
    h=[Line2D([],[],color=BLUE,lw=2.5,label="Original 4 scenarios (the ones people saw)"),
       Line2D([],[],color=ORANGE,lw=2.5,label="Mirrored 4 (same facts, opposite wording)")]
    fig.legend(handles=h,loc="lower center",ncol=2,fontsize=9,bbox_to_anchor=(0.5,-0.04),labelcolor=INK)
    fig.text(0.0,1.04,"The gap in original vs mirrored scenarios",fontsize=13,fontweight="semibold",color=INK)
    fig.text(0.0,1.005,"Point shapes follow Figure 1 (filled = swayed, open circle = not swayed, diamond = inconclusive). Shaded band = 95% CI.",fontsize=8.8,color=INK2)
    fig.tight_layout(h_pad=2.2)
    save(fig,"fig3_original_vs_mirrored")

# fig 4  one glance summary grid
def fig_grid():
    t=pd.read_csv(os.path.join(RES,"gap_all.csv"))
    fill={"swayed":"#256abf","inconclusive":"#9ec5f4","not swayed":"#f1f0ec"}
    txt={"swayed":"#ffffff","inconclusive":INK,"not swayed":INK}
    fig,ax=plt.subplots(figsize=(6.6,3.6))
    for r,m in enumerate(ORDER):
        for c,L in enumerate(LEVELS):
            row=t[(t.model==m)&(t.cards==L)].iloc[0]
            ax.add_patch(plt.Rectangle((c+0.04,r+0.06),0.92,0.88,color=fill[row.label],lw=0))
            ax.text(c+0.5,r+0.42,f"{row.gap:.0f}",ha="center",va="center",fontsize=11,fontweight="semibold",color=txt[row.label])
            ax.text(c+0.5,r+0.72,f"{row.pct_gain:.0f} vs {row.pct_loss:.0f}",ha="center",va="center",fontsize=7.2,color=txt[row.label],alpha=0.85)
    ax.set_xlim(0,4); ax.set_ylim(len(ORDER),0)
    ax.set_xticks([i+0.5 for i in range(4)]); ax.set_xticklabels([f"{L} cards" for L in LEVELS])
    ax.xaxis.tick_top()
    ax.set_yticks([i+0.5 for i in range(len(ORDER))]); ax.set_yticklabels(ORDER,color=INK)
    for s in ax.spines.values(): s.set_visible(False)
    h=[Patch(color=fill[k],label=k.capitalize()) for k in ["swayed","inconclusive","not swayed"]]
    ax.legend(handles=h,loc="upper center",bbox_to_anchor=(0.5,-0.02),ncol=3,fontsize=8.5,labelcolor=INK)
    ax.set_title("Wording gap in points (small text: safe % gain vs loss)",loc="left",color=INK,fontweight="semibold",fontsize=10.5,pad=26)
    fig.tight_layout()
    save(fig,"fig4_summary_grid")

if __name__=="__main__":
    fig_models(); fig_people(); fig_sets(); fig_grid()
    print("saved figures to",FIG)
