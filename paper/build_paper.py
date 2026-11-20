import re,os,sys,json
HERE=os.path.dirname(os.path.abspath(__file__))
SRC=open(os.path.join(HERE,"paper_source.md"),encoding="utf-8").read()

# author year labels for the doc version  same keys as refs.bib
CITE={"tversky1981framing":("Tversky & Kahneman","1981"),"kahneman1979prospect":("Kahneman & Tversky","1979"),
"kuhberger1998influence":("Kühberger","1998"),"levin1998all":("Levin et al.","1998"),"ellsberg1961risk":("Ellsberg","1961"),
"montibeller2015cognitive":("Montibeller & von Winterfeldt","2015"),"gernand2023set":("Gernand","2023"),
"binz2023using":("Binz & Schulz","2023"),"hagendorff2023human":("Hagendorff et al.","2023"),"suri2024large":("Suri et al.","2024"),
"macmillanscott2024irrationality":("Macmillan-Scott & Musolesi","2024"),"echterhoff2024cognitive":("Echterhoff et al.","2024"),
"sclar2024quantifying":("Sclar et al.","2024"),"sainz2023nlp":("Sainz et al.","2023"),"newcombe1998interval":("Newcombe","1998"),
"firth1993bias":("Firth","1993"),"liang1986longitudinal":("Liang & Zeger","1986"),"lakens2017equivalence":("Lakens","2017"),"ge2026mind":("Ge et al.","2026"),"zhang2026same":("Zhang et al.","2026"),"schultemecklenbeck2014out":("Schulte-Mecklenbeck and Kühberger","2014")}
FIGS={"FIG1":("figures/fig1_models_gap.pdf","1"),"FIG2":("figures/fig2_original_vs_mirrored.pdf","1"),"FIG3":("figures/fig3_people_gap.pdf","0.65")}

def blocks(text):
    # split into blocks separated by blank lines  tables kept whole
    return [b.strip("\n") for b in re.split(r"\n\s*\n",text) if b.strip()]

# ---------- doc markdown ----------
def doc_cites(s):
    s=re.sub(r"\[(@[^\]]+)\]",lambda m:"("+"; ".join(f"{CITE[k][0]}, {CITE[k][1]}" for k in re.findall(r"@(\w+)",m.group(1)))+")",s)
    s=re.sub(r"@(\w+)",lambda m:f"{CITE[m.group(1)][0]} ({CITE[m.group(1)][1]})" if m.group(1) in CITE else m.group(0),s)
    return s

def to_doc(blob_ids):
    out=[]
    for b in blocks(SRC):
        if b.startswith("# "): continue   # title lives in the doc title
        m=re.match(r"!\[(.*?)\]\((.*?)\)\{(FIG\d)\}",b)
        if m: out.append(f"![{m.group(1)}](blob/{blob_ids[m.group(3)]})"); continue
        if b.startswith("## References"):
            out.append("## References\n\n"+REFS_MD); continue
        out.append(doc_cites(b))
    return "\n\n".join(out)

# ---------- latex ----------
def esc(s):
    # escape latex specials in plain text  then restore markup we generate
    s=s.replace("\\","\\textbackslash{}")
    for a,b in [("&","\\&"),("%","\\%"),("$","\\$"),("#","\\#"),("_","\\_")]: s=s.replace(a,b)
    s=s.replace("±","$\\pm$").replace("−","$-$").replace("×","$\\times$").replace("–","--").replace("—","---")
    s=s.replace("<","$<$").replace(">","$>$")
    s=re.sub(r'"([^"]*)"',r"``\1''",s)
    return s

def inline(s):
    cites=[]
    def keep(m):
        cites.append(m.group(0)); return f"\x00{len(cites)-1}\x00"
    s=re.sub(r"\[(@[^\]]+)\]|@(\w+)",keep,s)
    urls=[]
    def keepu(m):
        urls.append(m.group(0)); return f"\x01{len(urls)-1}\x01"
    s=re.sub(r"https?://[^\s)]+[^\s).,;]",keepu,s)
    s=esc(s)
    s=re.sub(r"\x01(\d+)\x01",lambda m:"\\url{"+urls[int(m.group(1))]+"}",s)
    s=re.sub(r"\*\*(.+?)\*\*",r"\\textbf{\1}",s)
    s=re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",r"\\emph{\1}",s)
    def back(m):
        c=cites[int(m.group(1))]
        if c.startswith("["): return "\\citep{"+",".join(re.findall(r"@(\w+)",c))+"}"
        return "\\citet{"+c[1:]+"}"
    s=re.sub(r"\x00(\d+)\x00",back,s)
    s=s.replace("Section 3.5","Section~\\ref{sec:para}")
    return s

def table_tex(lines,caption,label,small=True):
    rows=[[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\|\s*-",l.strip())]
    n=len(rows[0])
    wide=any(len(c)>30 for r in rows for c in r) and n<=5
    if wide:
        spec="".join(">{\\raggedright\\arraybackslash}X" if i>0 or n<=4 else "l" for i in range(n))
        if n==5: spec="l"+">{\\raggedright\\arraybackslash}X"*4
        if n==4: spec=">{\\raggedright\\arraybackslash}X l "+">{\\raggedright\\arraybackslash}X"*2
        env=("\\begin{tabularx}{\\linewidth}{"+spec+"}","\\end{tabularx}")
    else:
        env=("\\begin{tabular}{l"+"c"*(n-2)+"l}" if n>2 else "\\begin{tabular}{ll}","\\end{tabular}")
    body="\\toprule\n"+" & ".join(inline(c) for c in rows[0])+" \\\\\n\\midrule\n"
    body+="\n".join(" & ".join(inline(c) for c in r)+" \\\\" for r in rows[1:])+"\n\\bottomrule"
    size="\\footnotesize" if (n>=6 or wide) else "\\small"
    return (f"\\begin{{table}}[ht]\n\\centering\n{size}\n\\caption{{{inline(caption)}}}\n\\label{{{label}}}\n\\setlength{{\\tabcolsep}}{{4pt}}\n"
            f"{env[0]}\n{body}\n{env[1]}\n\\end{{table}}")

def to_tex():
    bs=blocks(SRC); out=[]; i=0; in_app=False
    while i<len(bs):
        b=bs[i]
        if b.startswith("# "): i+=1; continue
        if b.startswith("## Abstract"):
            out.append("\\begin{abstract}\n"+inline(bs[i+1])+"\n\\end{abstract}"); i+=2; continue
        if b.startswith("## References"):
            out.append("\\bibliographystyle{abbrvnat}\n\\bibliography{refs}"); i+=1; continue
        if b.startswith("## Supplementary information"):
            out.append("\\clearpage\n\\section*{Supplementary information}\\label{app:materials}\n\\setcounter{table}{0}\\renewcommand{\\thetable}{S\\arabic{table}}\\setcounter{section}{0}\\renewcommand{\\thesection}{S}"); in_app=True; i+=1; continue
        m=re.match(r"^(#{2,3}) (.*)$",b)
        if m:
            lvl,t=len(m.group(1)),m.group(2)
            num=re.match(r"^([A-Z]\.\d+|\d+(\.\d+)?) (.*)$",t)
            if num: t=num.group(3)
            cmd=("section" if lvl==2 else "subsection")+("" if (num or in_app) else "*")
            lab="\\label{sec:para}" if num and num.group(1)=="3.5" else ""
            if t in ("Firth regressions","Safe choices by scenario"): out.append("\\clearpage")
            out.append(f"\\{cmd}{{{inline(t)}}}{lab}"); i+=1; continue
        mt=re.match(r"^\*\*Table (\w+)\.\*\* (.*)$",b,re.S)
        if mt and i+1<len(bs) and bs[i+1].startswith("|"):
            out.append(table_tex(bs[i+1].splitlines(),mt.group(2),"tab:"+mt.group(1).lower())); i+=2; continue
        mf=re.match(r"!\[(.*?)\]\((.*?)\)\{(FIG\d)\}",b)
        if mf:
            path,w=FIGS[mf.group(3)]
            cap=re.sub(r"^\*\*Figure \d+\.\*\* ","",bs[i+1]) if i+1<len(bs) and bs[i+1].startswith("**Figure") else mf.group(1)
            out.append(f"\\begin{{figure}}[t]\n\\centering\n\\includegraphics[width={w}\\linewidth]{{{path}}}\n\\caption{{{inline(cap)}}}\n\\label{{fig:{mf.group(3).lower()}}}\n\\end{{figure}}")
            i+=2 if i+1<len(bs) and bs[i+1].startswith("**Figure") else 1; continue
        if re.match(r"^\d+\. ",b):
            items=re.split(r"\n(?=\d+\. )",b); out.append("\\begin{enumerate}\n"+"\n".join("  \\item "+inline(re.sub(r"^\d+\. ","",x)) for x in items)+"\n\\end{enumerate}"); i+=1; continue
        if b.startswith("- "):
            items=re.split(r"\n(?=- )",b); out.append("\\begin{itemize}\n"+"\n".join("  \\item "+inline(x[2:]) for x in items)+"\n\\end{itemize}"); i+=1; continue
        mp=re.match(r"^\*\*([^*]+?\.)\*\* (.*)$",b,re.S)
        if mp and not in_app:
            out.append(f"\\paragraph{{{inline(mp.group(1))}}} "+inline(mp.group(2))); i+=1; continue
        t=inline(b)
        t=re.sub(r"\[(to confirm[^\]]*|To confirm[^\]]*|to add[^\]]*|Optional[^\]]*)\]",r"\\todo{\1}",t)
        out.append(t); i+=1
    return "\n\n".join(out)

PRE=r"""\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{mathptmx}
\usepackage[margin=1in]{geometry}
\usepackage{microtype}
\usepackage{amsmath}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{array}
\usepackage{xcolor}
\usepackage[round,authoryear]{natbib}
\usepackage[hidelinks,pdftitle={Information Access and Gain-Loss Framing in Six Large Language Models and Human Decision Makers},pdfauthor={Aadithya Chandramouli and Jeremy M. Gernand}]{hyperref}
\usepackage{caption}
\captionsetup{font=small,labelfont=bf}
\newcommand{\todo}[1]{\textcolor{red}{[#1]}}

\title{Information Access and Gain-Loss Framing in Six Large Language Models and Human Decision Makers}
\author{
  Aadithya Chandramouli\\
  School of Electrical Engineering and Computer Science\\
  College of Engineering, The Pennsylvania State University
  \and
  Jeremy M. Gernand\\
  College of Earth and Mineral Sciences\\
  The Pennsylvania State University
}
\date{}
\begin{document}
\maketitle
"""

REFS_MD=r"""Binz, M., & Schulz, E. (2023). Using cognitive psychology to understand GPT-3. *Proceedings of the National Academy of Sciences, 120*(6), e2218523120. doi:10.1073/pnas.2218523120

Echterhoff, J. M., Liu, Y., Alessa, A., McAuley, J., & He, Z. (2024). Cognitive bias in decision-making with LLMs. In *Findings of the Association for Computational Linguistics: EMNLP 2024* (pp. 12640–12653). doi:10.18653/v1/2024.findings-emnlp.739

Ellsberg, D. (1961). Risk, ambiguity, and the Savage axioms. *Quarterly Journal of Economics, 75*(4), 643–669.

Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika, 80*(1), 27–38. doi:10.1093/biomet/80.1.27

Gernand, J. M. (2023). A set of estimation and decision preference experiments for exploring risk assessment biases in engineering students. *ASCE-ASME Journal of Risk and Uncertainty in Engineering Systems, Part B: Mechanical Engineering, 9*(1), 011206. doi:10.1115/1.4055156

Hagendorff, T., Fabi, S., & Kosinski, M. (2023). Human-like intuitive behavior and reasoning biases emerged in large language models but disappeared in ChatGPT. *Nature Computational Science, 3*, 833–838. doi:10.1038/s43588-023-00527-x

Kahneman, D., & Tversky, A. (1979). Prospect theory: An analysis of decision under risk. *Econometrica, 47*(2), 263–291.

Kühberger, A. (1998). The influence of framing on risky decisions: A meta-analysis. *Organizational Behavior and Human Decision Processes, 75*(1), 23–55.

Lakens, D. (2017). Equivalence tests: A practical primer for t tests, correlations, and meta-analyses. *Social Psychological and Personality Science, 8*(4), 355–362. doi:10.1177/1948550617697177

Levin, I. P., Schneider, S. L., & Gaeth, G. J. (1998). All frames are not created equal: A typology and critical analysis of framing effects. *Organizational Behavior and Human Decision Processes, 76*(2), 149–188.

Liang, K.-Y., & Zeger, S. L. (1986). Longitudinal data analysis using generalized linear models. *Biometrika, 73*(1), 13–22. doi:10.1093/biomet/73.1.13

Macmillan-Scott, O., & Musolesi, M. (2024). (Ir)rationality and cognitive biases in large language models. *Royal Society Open Science, 11*(6), 240255. doi:10.1098/rsos.240255

Montibeller, G., & von Winterfeldt, D. (2015). Cognitive and motivational biases in decision and risk analysis. *Risk Analysis, 35*(7), 1230–1251. doi:10.1111/risa.12360

Newcombe, R. G. (1998). Interval estimation for the difference between independent proportions: Comparison of eleven methods. *Statistics in Medicine, 17*(8), 873–890.

Sainz, O., Campos, J., García-Ferrero, I., Etxaniz, J., Lopez de Lacalle, O., & Agirre, E. (2023). NLP evaluation in trouble: On the need to measure LLM data contamination for each benchmark. In *Findings of the Association for Computational Linguistics: EMNLP 2023* (pp. 10776–10787). doi:10.18653/v1/2023.findings-emnlp.722

Sclar, M., Choi, Y., Tsvetkov, Y., & Suhr, A. (2024). Quantifying language models' sensitivity to spurious features in prompt design or: How I learned to start worrying about prompt formatting. *International Conference on Learning Representations (ICLR)*.

Suri, G., Slater, L. R., Ziaee, A., & Nguyen, M. (2024). Do large language models show decision heuristics similar to humans? A case study using GPT-3.5. *Journal of Experimental Psychology: General, 153*(4), 1066–1075. doi:10.1037/xge0001547

Tversky, A., & Kahneman, D. (1981). The framing of decisions and the psychology of choice. *Science, 211*(4481), 453–458. doi:10.1126/science.7455683"""
if __name__=="__main__":
    body=to_tex()
    open(os.path.join(HERE,"main.tex"),"w",encoding="utf-8").write(PRE+body+"\n\n\\end{document}\n")
    print("wrote main.tex")
