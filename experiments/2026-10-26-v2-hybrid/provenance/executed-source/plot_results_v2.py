"""Descriptive research plots. No human accuracy estimates or model-score comparisons."""
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/figures_v2'
OUT.mkdir(exist_ok=True)
os.environ['MPLCONFIGDIR']=str(ROOT/'data/interim/matplotlib')
os.environ['XDG_CACHE_HOME']=str(ROOT/'data/interim/plot_cache')
import csv,json,hashlib,itertools,textwrap,zipfile
from collections import defaultdict,Counter
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

def read(path):
    with (ROOT/path).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def csvout(name,rows):
    with (OUT/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

inputs=['outputs/v2_20261026_pool_audit/contributions_not_for_reviewers.csv',
    'outputs/v2_run_summary.csv','outputs/v2_unlabelled_agreement.csv',
    'review/sample.csv','review/blinded_candidate_pool.csv',
    'review/v2_20261026/blinded_candidate_pool.csv','data/processed/masco_groups.csv',
    'configs/review_pool_v2.json','outputs/v2_rerank_review/run.json']
frozen={}
for manifest in ['file_checksums.sha256','outputs/v2_file_checksums.sha256']:
    for line in (ROOT/manifest).read_text().splitlines():
        h,p=line.split(None,1);frozen[p.lstrip('*')]=h
hashes={p:digest(ROOT/p) for p in inputs}
for p,h in hashes.items():
    if p not in frozen or frozen[p]!=h:raise ValueError('Input not verified by existing freeze: '+p)
sample=read('review/sample.csv');codes=sorted(r['masco_code'] for r in sample);n=len(codes)
cfg=json.loads((ROOT/'configs/review_pool_v2.json').read_text())
methods=[tuple(x) for x in cfg['expected_methods']]
ranked=defaultdict(dict)
for r in read(inputs[0]):
    key=(r['method'],r['input_variant'],r['masco_code']);rank=int(r['rank'])
    if rank in ranked[key] and ranked[key][rank]!=r['esco_uri']:raise ValueError('Conflicting repeated channel')
    ranked[key][rank]=r['esco_uri']
tops={}
for method,variant in methods:
    for code in codes:
        r=ranked[(method,variant,code)]
        if set(r)!=set(range(1,11)):raise ValueError('Incomplete top ten')
        tops[(method,variant,code)]=[r[i] for i in range(1,11)]

enc=['minilm','qwen_embedding','gemma2','jina5_retrieval']
names=['MiniLM','Qwen3','EmbeddingGemma 2','Jina v5']
short=['MiniLM','Qwen3','Gemma 2','Jina v5']
def agreement(a,b):
    shared=[];first=[]
    for code in codes:
        x=tops[(*a,code)];y=tops[(*b,code)]
        shared.append(len(set(x)&set(y))/10*100);first.append(float(x[0]==y[0])*100)
    return float(np.mean(shared)),float(np.mean(first))
reference=('hybrid_minilm','title_context')
all_metrics=[]
for method in methods:
    shared,first=agreement(method,reference)
    all_metrics.append(dict(method=method[0],input_variant=method[1],sources=n,
        shared_top10_percent=shared,same_top1_percent=first,reference='hybrid_minilm / title_context'))
for row in read('outputs/v2_unlabelled_agreement.csv'):
    check=next(x for x in all_metrics if (x['method'],x['input_variant'])==(row['method'],row['variant']))
    if not np.isclose(check['shared_top10_percent'],float(row['mean_shared_top10'])*10):raise ValueError('Prior summary differs')
    if not np.isclose(check['same_top1_percent'],int(row['same_top1_count'])/n*100):raise ValueError('Prior top1 summary differs')
csvout('all_method_agreement.csv',all_metrics)
pairrows=[];matrices={}
for stage in ['hybrid','reranked']:
    shared=np.zeros((4,4));first=np.zeros((4,4))
    for i,j in itertools.product(range(4),repeat=2):
        a=('hybrid_'+enc[i]+('_qwen3_reranked' if stage=='reranked' else ''),'title_context')
        b=('hybrid_'+enc[j]+('_qwen3_reranked' if stage=='reranked' else ''),'title_context')
        shared[i,j],first[i,j]=agreement(a,b)
        if i<j:pairrows.append(dict(stage=stage,encoder_a=names[i],encoder_b=names[j],
            shared_top10_percent=shared[i,j],same_top1_percent=first[i,j],sources=n))
    matrices[stage]=(shared,first)
csvout('encoder_pair_agreement.csv',pairrows)
effects=[]
for key,name in zip(enc,names):
    shared,first=agreement(('hybrid_'+key,'title_context'),('hybrid_'+key+'_qwen3_reranked','title_context'))
    effects.append(dict(encoder=name,top1_changed_percent=100-first,top10_replaced_percent=100-shared,sources=n))
csvout('reranking_changes.csv',effects)
original=read('review/blinded_candidate_pool.csv');expanded=read('review/v2_20261026/blinded_candidate_pool.csv')
oldset={(r['masco_code'],r['esco_uri']) for r in original};newset={(r['masco_code'],r['esco_uri']) for r in expanded}
union={(code,u) for (m,v,code),us in tops.items() for u in us}
if not oldset<=newset or union!=newset:raise ValueError('Pool union differs')
groups={r['code']:r['title_original'] for r in read('data/processed/masco_groups.csv') if r['level']=='major'}
major={r['masco_code']:r['major_group'] for r in sample}
oldcounts=Counter(major[c] for c,_ in oldset);newcounts=Counter(major[c] for c,_ in newset)
group_rows=[dict(major_group=g,title=groups[g],sampled_sources=sum(major[c]==g for c in codes),
    original_pairs=oldcounts[g],expanded_pairs=newcounts[g],added_pairs=newcounts[g]-oldcounts[g]) for g in sorted(groups)]
csvout('pool_growth_by_group.csv',group_rows)

BG='#fbfcfe';INK='#172b4d';BLUE='#2874a6';TEAL='#169b91';ORANGE='#df8f32';PURPLE='#7960aa';GREY='#9aa8b8'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':13,'axes.titleweight':'bold',
    'axes.labelcolor':INK,'text.color':INK,'xtick.color':INK,'ytick.color':INK,'axes.edgecolor':'#d9e0e9',
    'figure.facecolor':BG,'axes.facecolor':BG,'svg.fonttype':'none','savefig.facecolor':BG})
figures=[]
def tidy(ax,percent=False):
    ax.spines[['top','right']].set_visible(False)
    ax.set_axisbelow(True);ax.grid(axis='x',color='#e3e8ef',linewidth=.7)
    if percent:ax.set_xlim(0,100);ax.xaxis.set_major_formatter(PercentFormatter(100))
def save(fig,name,caption):
    fig.savefig(OUT/(name+'.png'),dpi=180,bbox_inches='tight')
    fig.savefig(OUT/(name+'.svg'),bbox_inches='tight')
    figures.append(dict(file=name,caption=caption));plt.close(fig)
def title(fig,heading,subtitle):
    fig.suptitle(heading,x=.06,y=.975,ha='left',fontsize=22,fontweight='bold')
    fig.text(.06,.936,subtitle,fontsize=11,color='#526579',ha='left')

# Overview: quantities with different source counts never share a runtime axis.
fig,axs=plt.subplots(2,2,figsize=(14,10))
fig.subplots_adjust(left=.12,right=.97,top=.86,bottom=.15,hspace=.50,wspace=.42)
title(fig,'MASCO–ESCO experiment comparison','Observed rankings and workload • no human accuracy labels • MASCO 2020 / ESCO 1.2.1')
runtime={r['run_id']:float(r['elapsed_seconds']) for r in read('outputs/v2_run_summary.csv')}
times=[runtime[x] for x in ['v2_minilm_full','v2_qwen_full','v2_gemma2_full','v2_jina5_full']]
csvout('retrieval_runtime.csv',[dict(encoder=name,sources=6620,targets=3039,elapsed_seconds=seconds,
    scope='Full retrieval including model loading and output work; one observed local run') for name,seconds in zip(names,times)])
ax=axs[0,0];bars=ax.barh(short,times,color=BLUE,height=.6);ax.invert_yaxis();tidy(ax)
ax.bar_label(bars,labels=[f'{x:.1f} s' for x in times],padding=5,fontsize=10)
ax.set_xlim(0,max(times)*1.25);ax.set_title('A  Full retrieval runtime',loc='left',pad=12)
ax.set_xlabel('Seconds · 6,620 sources per run')
ax=axs[0,1];y=np.arange(4);h=.3
for offset,key,color,label in [(-h/2,'top1_changed_percent',ORANGE,'First candidate changed'),(h/2,'top10_replaced_percent',TEAL,'Top-10 candidates replaced')]:
    vals=[x[key] for x in effects]
    bars=ax.barh(y+offset,vals,h,color=color,label=label)
    ax.bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=4,fontsize=9)
ax.set_yticks(y,short);ax.invert_yaxis();tidy(ax,True)
ax.set_title('B  Qwen reranking changes',loc='left',pad=12)
ax.set_xlabel('Versus each encoder’s own hybrid ranking\n330 review sources')
ax.set_ylim(3.6,-.9)
ax.legend(loc='upper right',fontsize=9,frameon=False)
ax=axs[1,0];old=len(oldset);new=len(newset);added=new-old
ax.barh([1,0],[old,old],color=BLUE,height=.55,label='Original pairs')
ax.barh([0],[added],left=[old],color=TEAL,height=.55,label='Additional pairs')
ax.text(old/2,1,f'{old:,}',ha='center',va='center',color='white',fontweight='bold')
ax.text(old/2,0,f'{old:,}',ha='center',va='center',color='white',fontweight='bold')
ax.text(old+added/2,0,f'+{added:,}',ha='center',va='center',color='white',fontweight='bold')
ax.text(new+200,0,f'{new:,}',va='center',fontweight='bold')
ax.set_yticks([1,0],['Original\n6 combinations','Expanded\n20 combinations']);ax.set_xlim(0,new*1.22);tidy(ax)
ax.set_title('C  Blinded review pool',loc='left',pad=12)
ax.set_xlabel('Distinct source–target pairs · same 330 sources')
ax=axs[1,1];stagevals=[]
for stage in ['hybrid','reranked']:
    arr=[x for x in pairrows if x['stage']==stage]
    stagevals.append([np.mean([x[k] for x in arr]) for k in ['shared_top10_percent','same_top1_percent']])
y=np.arange(2)
for j,(col,label) in enumerate([(BLUE,'Shared top 10'),(PURPLE,'Same first candidate')]):
    bars=ax.barh(y+(j-.5)*.3,[v[j] for v in stagevals],.3,color=col,label=label)
    ax.bar_label(bars,labels=[f'{v[j]:.1f}%' for v in stagevals],padding=4,fontsize=9)
ax.set_yticks(y,['Hybrid','Qwen-reranked']);ax.invert_yaxis();tidy(ax);ax.set_xlim(0,115);ax.set_xticks([0,25,50,75,100]);ax.xaxis.set_major_formatter(PercentFormatter(100))
ax.set_title('D  Agreement between encoders',loc='left',pad=12)
ax.set_xlabel('Average across 6 encoder pairs · 330 sources')
ax.set_ylim(1.45,-.9)
ax.legend(loc='upper right',fontsize=9,frameon=False)
fig.text(.06,.045,'Agreement and candidate changes are not accuracy. Common reranking can make models agree without making them correct.\nRuntime includes loading, retrieval and output work on this Mac; one observed run per encoder, not a controlled speed benchmark.',fontsize=10,color='#526579')
save(fig,'01_overview','Runtime, reranking changes, pool growth, and cross-encoder agreement. Descriptive only.')

# Full baseline/alternative comparison, with a clearly identified reference.
labels=[];colors=[]
for m,v in methods:
    if m in ['lexical_tfidf','minilm','weighted_minilm_adaptation']:
        base={'lexical_tfidf':'Original TF-IDF','minilm':'Original MiniLM','weighted_minilm_adaptation':'Original weighted MiniLM'}[m]
        labels.append(base+(' · title' if v=='title' else ' · context'));colors.append(GREY)
    elif m in ['bm25','tfidf']:
        labels.append('BM25' if m=='bm25' else 'Matched-input TF-IDF');colors.append(BLUE)
    else:
        key=next(e for e in sorted(enc,key=len,reverse=True) if m in [f'dense_{e}',f'hybrid_{e}',f'hybrid_{e}_qwen3_reranked'])
        stage='Reranked' if m.endswith('_qwen3_reranked') else ('Dense' if m.startswith('dense_') else 'Hybrid')
        labels.append(f'{stage} · {names[enc.index(key)]}'+('  [reference]' if (m,v)==reference else ''))
        colors.append({'Reranked':PURPLE,'Dense':TEAL,'Hybrid':ORANGE}[stage])
fig,axs=plt.subplots(1,2,figsize=(15,12.5),sharey=True)
fig.subplots_adjust(left=.30,right=.96,top=.87,bottom=.10,wspace=.12)
title(fig,'All 20 method/input combinations','Similarity to the matched-input MiniLM hybrid • 330 review occupations • higher agreement does not mean higher quality')
y=np.arange(20)
for ax,key,heading in zip(axs,['shared_top10_percent','same_top1_percent'],['Shared top-10 candidates','Same first candidate']):
    vals=[r[key] for r in all_metrics]
    bars=ax.barh(y,vals,color=colors,height=.7)
    ax.bar_label(bars,labels=[f'{v:.1f}%' for v in vals],padding=4,fontsize=9)
    ax.set_yticks(y,labels);ax.set_xlim(0,115);ax.set_xticks([0,25,50,75,100]);ax.xaxis.set_major_formatter(PercentFormatter(100));tidy(ax)
    ax.set_title(heading,loc='left',pad=16)
    for split in [5.5,7.5,11.5,15.5]:ax.axhline(split,color='#d9e0e9',lw=.8)
axs[0].invert_yaxis()
fig.text(.06,.04,'Reference = the new MiniLM hybrid, not the original baseline. Shared top 10 is the average intersection size divided by 10.\nHistorical baselines differ in title cleaning and alias inputs; the four new encoders use matched inputs. These are descriptive sample statistics.',fontsize=10,color='#526579')
save(fig,'02_all_methods','All methods compared with the matched-input MiniLM hybrid. Agreement is not correctness.')

fig,axs=plt.subplots(2,2,figsize=(13,11))
fig.subplots_adjust(left=.12,right=.90,top=.86,bottom=.12,wspace=.24,hspace=.35)
title(fig,'Do the encoders retrieve the same occupations?','Same 330 sources · a common Qwen reranker reduces variation between retrieval pools')
for col,stage in enumerate(['hybrid','reranked']):
    for row in range(2):
        ax=axs[row,col];values=matrices[stage][row]
        im=ax.imshow(values,vmin=0,vmax=100,cmap='YlGnBu',aspect='equal')
        ax.set_xticks(range(4),short,rotation=25,ha='right');ax.set_yticks(range(4),short)
        ax.set_title(('Hybrid' if stage=='hybrid' else 'After Qwen reranking')+'\n'+('Shared top 10 (%)' if row==0 else 'Same first candidate (%)'),pad=14)
        for i,j in itertools.product(range(4),repeat=2):
            ax.text(j,i,f'{values[i,j]:.1f}',ha='center',va='center',color='white' if values[i,j]>65 else INK,fontsize=12,fontweight='bold')
        for spine in ax.spines.values():spine.set_visible(False)
cax=fig.add_axes([.93,.23,.018,.51]);fig.colorbar(im,cax=cax,label='Agreement (%)')
fig.text(.06,.045,'Each cell compares two encoders; diagonal cells are 100% by definition. The same color scale is used throughout.\nNear-identical reranked results show convergence, not independent confirmation of the correct MASCO–ESCO mapping.',fontsize=10,color='#526579')
save(fig,'03_encoder_agreement','Pairwise encoder agreement before and after common reranking. Same 0–100% scale.')

fig,ax=plt.subplots(figsize=(14,9.5));fig.subplots_adjust(left=.37,right=.95,top=.86,bottom=.13)
title(fig,'Where did the review pool expand?','Original pairs retained, with new candidates added from the expanded method set • 33 sources per major group')
y=np.arange(10);oldvals=[r['original_pairs'] for r in group_rows];adds=[r['added_pairs'] for r in group_rows]
ax.barh(y,oldvals,color=BLUE,height=.67,label='Original pool');ax.barh(y,adds,left=oldvals,color=TEAL,height=.67,label='Additional pairs')
labs=[str(r['major_group'])+'  '+textwrap.fill(r['title'].title(),38) for r in group_rows]
ax.set_yticks(y,labs);ax.invert_yaxis();tidy(ax)
maxcount=max(r['expanded_pairs'] for r in group_rows);ax.set_xlim(0,maxcount*1.23)
for i,r in enumerate(group_rows):ax.text(r['expanded_pairs']+20,i,f'{r["expanded_pairs"]:,}  (+{r["added_pairs"]:,})',va='center',fontsize=10)
ax.set_xlabel('Distinct source–target candidate pairs');ax.legend(frameon=False,loc='lower right',bbox_to_anchor=(1,1.01))
fig.text(.06,.045,'Each group contains the same number of sampled occupations. More pairs indicate broader review coverage and more review work, not better accuracy.\nThe sample includes calibration, probability-test and purposive challenge cases; these counts are not estimates for the full workforce.',fontsize=10,color='#526579')
save(fig,'04_pool_by_group','Blinded pool growth by MASCO major group, with 33 sampled sources in each group.')

summary=dict(review_sources=n,methods=len(methods),original_pairs=len(oldset),expanded_pairs=len(newset),
    added_pairs=len(newset-oldset),reranking_changes=effects,
    mean_encoder_agreement={stage:dict(shared_top10_percent=float(np.mean([r['shared_top10_percent'] for r in pairrows if r['stage']==stage])),same_top1_percent=float(np.mean([r['same_top1_percent'] for r in pairrows if r['stage']==stage]))) for stage in ['hybrid','reranked']},
    human_accuracy_available=False,input_hashes=hashes,script_sha256=digest(Path(__file__)),
    dependencies={'matplotlib':matplotlib.__version__,'numpy':np.__version__},figures=figures)
(OUT/'plot_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
(OUT/'README.txt').write_text('MASCO 2020 / ESCO 1.2.1 comparison graphs\n\n'
    '01: Runtime, reranking changes, review-pool growth and average encoder agreement.\n'
    '02: All 20 method/input combinations compared with the matched-input MiniLM hybrid.\n'
    '03: Pairwise encoder agreement before and after common Qwen reranking.\n'
    '04: Review-pool growth by MASCO major group.\n\n'
    'PNG files are high-resolution previews; SVG files are scalable vector figures. CSV files contain plotted values.\n'
    'Ranking comparisons use the fixed 330-source review sample. Runtime uses 6,620 sources per retrieval run.\n'
    'Shared top 10 = average intersection size divided by 10. Same first candidate = fraction with the same rank-1 target.\n'
    'No human reference labels exist: agreement, pool size and ranking changes are not accuracy or improvement metrics.\n')
with zipfile.ZipFile(OUT/'comparison_graphs.zip','w',zipfile.ZIP_DEFLATED) as archive:
    for p in sorted(OUT.iterdir()):
        if p.suffix in ['.png','.svg','.csv','.json','.txt']:archive.write(p,p.name)
print(json.dumps({k:summary[k] for k in ['review_sources','methods','original_pairs','expanded_pairs','reranking_changes','mean_encoder_agreement']},indent=2))
