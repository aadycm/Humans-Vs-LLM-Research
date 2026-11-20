import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

HERE=os.path.dirname(os.path.abspath(__file__))
RES=os.path.join(os.path.dirname(HERE),"results","followup")
OUT=os.path.join(os.path.dirname(HERE),"paper","figures")   # pdf versions for the latex build
PNG=os.path.join(os.path.dirname(HERE),"figures","paper")    # png versions for browsing
os.makedirs(OUT,exist_ok=True); os.makedirs(PNG,exist_ok=True)

# plain journal look  times font to match the paper  no titles inside the figure
plt.rcParams.update({"font.family":"TeX Gyre Termes","font.size":9,"axes.labelsize":9,"axes.titlesize":9.5,
                     "xtick.labelsize":8.5,"ytick.labelsize":8.5,"legend.fontsize":8.5,"axes.linewidth":0.6,
                     "xtick.major.width":0.6,"ytick.major.width":0.6,"xtick.major.size":3,"ytick.major.size":3,
                     "pdf.fonttype":42,"savefig.bbox":"tight","savefig.pad_inches":0.02})
BLUE,ORANGE,GREY="#2a78d6","#e0682f","#555555"
ORDER=["GPT-4.1","GPT-4o","Qwen3 235B","Gemini 2.5 Flash","Llama 4 Maverick","GPT-4o-mini"]
LEVELS=[0,2,3,4]
# marker shape carries the label so its readable in black and white too
MK={"swayed":("o",True),"within threshold":("o",False),"inconclusive":("s",False)}

def axes_style(ax,xs):
    ax.axhspan(-10,10,color="#ececec",lw=0,zorder=0)   # the plus minus 10 point zone from the rule
    ax.axhline(0,color="#9a9a9a",lw=0.6,zorder=1)
    ax.set_xticks(xs); ax.set_xlim(xs[0]-0.5,xs[-1]+0.5)
    for s in ["top","right"]: ax.spines[s].set_visible(False)

def draw(ax,g,x,color,ms=4.5,join="cards"):
    x=list(x); y=list(g.gap); lo=list(g.lo); hi=list(g.hi)
    # no line from 0 cards to 2 cards since the prompt format changes there, and no lines at all for the human groups
    if join=="cards": ax.plot(x[1:],y[1:],color=color,lw=1.1,zorder=2)
    ax.errorbar(x,y,yerr=[[a-b for a,b in zip(y,lo)],[b-a for a,b in zip(y,hi)]],fmt="none",ecolor=color,elinewidth=0.8,capsize=2,zorder=2)
    for xi,yi,lab in zip(x,y,g.label):
        m,filled=MK[lab]
        ax.plot(xi,yi,m,ms=ms,mec=color,mew=1,mfc=color if filled else "white",zorder=3)

def label_legend(color=GREY):
    return [Line2D([],[],marker="o",ls="",ms=4.5,mec=color,mfc=color,label="Swayed"),
            Line2D([],[],marker="o",ls="",ms=4.5,mec=color,mfc="white",label="Within threshold"),
            Line2D([],[],marker="s",ls="",ms=4.5,mec=color,mfc="white",label="Inconclusive"),
            plt.Rectangle((0,0),1,1,color="#ececec",label="Within ±10 points")]

def fig1():
    t=pd.read_csv(os.path.join(RES,"gap_balanced.csv"))   # balanced view is the main result now
    fig,axs=plt.subplots(2,3,figsize=(6.5,3.9),sharex=True,sharey=True)
    for ax,m in zip(axs.ravel(),ORDER):
        axes_style(ax,LEVELS); draw(ax,t[t.model==m].sort_values("cards"),LEVELS,BLUE)
        ax.set_title(m); ax.set_ylim(-15,100)
    fig.supylabel("Wording gap (percentage points)",fontsize=9,x=0.01)   # one shared label so the two rows dont collide
    for ax in axs[1]: ax.set_xlabel("Card limit")
    fig.legend(handles=label_legend(),loc="lower center",ncol=4,frameon=False,bbox_to_anchor=(0.5,-0.05))
    fig.tight_layout(rect=(0,0.04,1,1))
    fig.savefig(os.path.join(OUT,"fig1_models_gap.pdf")); fig.savefig(os.path.join(PNG,"fig1_models_gap.png"),dpi=300); plt.close(fig)

def fig2():
    o=pd.read_csv(os.path.join(RES,"gap_originals_origwording.csv")); mi=pd.read_csv(os.path.join(RES,"gap_mirrored.csv"))   # the two halves of the balanced view  60 runs per side each
    fig,axs=plt.subplots(2,3,figsize=(6.5,3.9),sharex=True,sharey=True)
    for ax,m in zip(axs.ravel(),ORDER):
        axes_style(ax,LEVELS)
        # small horizontal nudge so the two sets of error bars dont sit on top of each other
        draw(ax,o[o.model==m].sort_values("cards"),[L-0.08 for L in LEVELS],BLUE,ms=4)
        draw(ax,mi[mi.model==m].sort_values("cards"),[L+0.08 for L in LEVELS],ORANGE,ms=4)
        ax.set_title(m); ax.set_ylim(-15,100)
    fig.supylabel("Wording gap (percentage points)",fontsize=9,x=0.01)   # one shared label so the two rows dont collide
    for ax in axs[1]: ax.set_xlabel("Card limit")
    h=[Line2D([],[],color=BLUE,lw=1.1,marker="o",ms=4,label="Q1 to Q4"),
       Line2D([],[],color=ORANGE,lw=1.1,marker="o",ms=4,label="M1 to M4")]
    fig.legend(handles=h,loc="lower center",ncol=2,frameon=False,bbox_to_anchor=(0.5,-0.05))
    fig.tight_layout(rect=(0,0.04,1,1))
    fig.savefig(os.path.join(OUT,"fig2_original_vs_mirrored.pdf")); fig.savefig(os.path.join(PNG,"fig2_original_vs_mirrored.png"),dpi=300); plt.close(fig)

def fig3():
    g=pd.read_csv(os.path.join(RES,"human_gap_grouped.csv"))
    bt=pd.read_csv(os.path.join(RES,"human_boot.csv"))   # participant bootstrap intervals are the main ones now
    g["lo"]=bt.boot_lo.values; g["hi"]=bt.boot_hi.values
    fig,ax=plt.subplots(figsize=(3.8,2.4))
    xs=[0,1,2]
    axes_style(ax,xs); draw(ax,g,xs,GREY,ms=5,join=None)
    ax.set_xticklabels([f"0 or 1\n(n={g.n_gain[0]+g.n_loss[0]})",f"2 or 3\n(n={g.n_gain[1]+g.n_loss[1]})",f"4\n(n={g.n_gain[2]+g.n_loss[2]})"])
    ax.set_xlabel("Cards opened"); ax.set_ylabel("Wording gap (percentage points)"); ax.set_ylim(-25,40)
    # legend outside on the right so it never sits on the error bars
    ax.legend(handles=label_legend(),loc="center left",bbox_to_anchor=(1.01,0.5),frameon=False,fontsize=7.5,handlelength=1.2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT,"fig3_people_gap.pdf")); fig.savefig(os.path.join(PNG,"fig3_people_gap.png"),dpi=300); plt.close(fig)

if __name__=="__main__":
    fig1(); fig2(); fig3(); print("saved to",OUT,"and",PNG)
