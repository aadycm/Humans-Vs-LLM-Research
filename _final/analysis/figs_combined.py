"""python figs_combined.py <outdir with combined_trials.csv>"""
import sys, os, numpy as np, pandas as pd, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statsmodels.stats.proportion import proportion_confint
out = sys.argv[1]; D = pd.read_csv(os.path.join(out, 'combined_trials.csv'))
B, O, INK, MUT, GRID = '#2a78d6', '#eb6834', '#0b0b0b', '#52514e', '#e4e3df'
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.edgecolor': MUT, 'xtick.color': MUT, 'ytick.color': MUT})
srcs = ['human'] + sorted(s for s in D.source.unique() if s != 'human')
names = {'human': 'Humans (n=198)', 'gpt-4o': 'GPT-4o', 'gpt-4.1': 'GPT-4.1', 'gpt-4o-mini': 'GPT-4o-mini'}
def panel(measure, fname, ylab, ref, reflab, ymax):
    fig, axs = plt.subplots(1, len(srcs), figsize=(7.2, 2.9), sharey=True)
    for ax, s in zip(axs, srcs):
        d = D[D.source == s]; ax.yaxis.grid(True, color=GRID, lw=.8); ax.set_axisbelow(True)
        for i, (fr, col) in enumerate([('gain', B), ('loss', O)]):
            ps, lo, hi = [], [], []
            for am in ['precise', 'ambiguous']:
                c = d[(d.frame == fr) & (d.ambiguity == am)]
                if measure == 'threat':
                    c = c[c.nOpened > 0]; k, n = int(c.nThreat.sum()), int(c.nOpened.sum())
                else:
                    k, n = int(c.safe.sum()), len(c)
                a, b = proportion_confint(k, n, method='wilson') if n else (np.nan, np.nan)
                ps.append(100 * k / n if n else np.nan); lo.append(100 * a); hi.append(100 * b)
            x = np.arange(2) + (i - .5) * .38
            ax.bar(x, ps, .36, color=col, label=f'{fr.capitalize()} frame')
            ax.errorbar(x, ps, yerr=[np.clip(np.subtract(ps, lo), 0, None), np.clip(np.subtract(hi, ps), 0, None)], fmt='none', ecolor=INK, capsize=2.5, lw=1)
        ax.axhline(ref, ls='--', color=MUT, lw=1, label=reflab)
        ax.set_xticks([0, 1], ['Precise', 'Ambig.']); ax.set_title(names.get(s, s), fontsize=9.5, color=INK, loc='left'); ax.set_ylim(0, ymax)
    axs[0].set_ylabel(ylab); h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, loc='upper center', ncol=3, frameon=False, fontsize=8.5, bbox_to_anchor=(.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, .9)); fig.savefig(os.path.join(out, fname), dpi=220)
panel('threat', 'fig_threat_by_agent.png', 'Threat cards, % of opened', 300 / 7, 'Chance (43%)', 75)
panel('safe', 'fig_safe_by_agent.png', 'Chose safe option, %', 50, '50%', 110)
