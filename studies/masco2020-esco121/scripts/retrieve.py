"""Fresh candidates only. Scores are not confidence, probabilities, or decisions."""
import argparse, os, time, random, re, unicodedata, platform, importlib.metadata
os.environ.setdefault('TOKENIZERS_PARALLELISM','false')
os.environ.setdefault('HF_HUB_OFFLINE','1')
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from difflib import SequenceMatcher
from common import *
REV='1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
def norm(s):return ' '.join(re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()))
def clean(s):
 s=re.sub(r'\s+Grade\s+.*$','',s,flags=re.I)
 s=re.sub(r'^Competent Person\s*\(CP\)\s*-\s*','',s,flags=re.I)
 return ' '.join(s.split()).strip()
def ranked(values,indices,k):return sorted(indices,key=lambda j:(-float(values[j]),j))[:k]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--scope',choices=['smoke','full'],default='smoke');ap.add_argument('--k',type=int,default=10);ap.add_argument('--run-id',help='New immutable output directory name for a reproduction run');a=ap.parse_args()
 seed=20261026;random.seed(seed);np.random.seed(seed)
 import torch
 torch.manual_seed(seed);torch.set_num_threads(4)
 start=time.time();roles=read_csv(ROOT/'data/processed/masco_occupations.csv');esco=read_csv(ROOT/'data/processed/esco_occupations.csv')
 ctx={r['code']:r for r in read_csv(ROOT/'data/processed/masco_group_context.csv')}
 if a.scope=='smoke':
  rng=random.Random(seed);roles=[r for g in '0123456789' for r in rng.sample([r for r in roles if r['major_group']==g],3)]
 run=a.run_id or f'{a.scope}_20261026_k{a.k}'
 if not re.fullmatch(r'[A-Za-z0-9_-]+',run):raise ValueError('Unsafe run id')
 outdir=ROOT/'outputs'/run
 if (outdir/'candidates.csv').exists():raise FileExistsError('Frozen run exists; pass --run-id with a new name')
 outdir.mkdir(exist_ok=True)
 inputs=[];qtitle=[];qprofile=[]
 for r in roles:
  title=clean(r['title_original']);c=ctx.get(r['parent_code'],{})
  # Group description remains explicitly qualified; no portal profiles are imported.
  context=' '.join(c.get('description','').split())
  profile=title+('. Unit-group context (not an individual description): '+context if context else '')
  qtitle.append(title);qprofile.append(profile)
  inputs.append(dict(code=r['code'],major_group=r['major_group'],original_title=r['title_original'],title_input=title,profile_input=profile,context_scope='unit_group' if context else '',context_code=r['parent_code'] if context else '',context_pdf_page=c.get('pdf_page_start',''),source_sha256=r['source_sha256']))
 etitle=[r['title_original'] for r in esco];eprofile=[r['title_original']+'. '+r['description'] for r in esco]
 labels=[[r['title_original']]+r['alt_labels'].splitlines() for r in esco]
 normalized_labels=[[norm(x) for x in labs] for labs in labels]
 from collections import defaultdict
 exact_index=defaultdict(set)
 for j,labs in enumerate(normalized_labels):
  for lab in labs:exact_index[lab].add(j)
 modeldir=ROOT/f'sources/raw/minilm_{REV}'
 model=SentenceTransformer(str(modeldir),local_files_only=True,device='cpu')
 encode=lambda xs:model.encode(xs,batch_size=64,normalize_embeddings=True,show_progress_bar=True,convert_to_numpy=True)
 # Content-addressed target cache, including full input content and model bytes.
 key=__import__('hashlib').sha256(json.dumps([etitle,eprofile,REV,sha(modeldir/'model.safetensors')]).encode()).hexdigest()
 cache=ROOT/'data/interim'/f'esco_vectors_{key}.npz'
 if cache.exists():z=np.load(cache);en,ep=z['title'],z['profile']
 else:en,ep=encode(etitle),encode(eprofile);np.savez_compressed(cache,title=en,profile=ep)
 qn,qp=encode(qtitle),encode(qprofile);tn=qn@en.T;tp=qp@ep.T
 for r,tt,pt in zip(inputs,qtitle,qprofile):
  r['title_tokens']=len(model.tokenizer.encode(tt));r['profile_tokens']=len(model.tokenizer.encode(pt));r['profile_truncated']=r['profile_tokens']>model.max_seq_length
 write_csv(outdir/'query_inputs.csv',inputs)
 pairfields=['run_id','method','input_variant','masco_version','masco_code','esco_version','esco_uri','esco_code','rank','score','score_type','title_cosine','profile_cosine','lexical_component','matched_label','label_boost','candidate_origin','review_status']
 candidates=[];method_counts={}
 for variant in ['title','title_context']:
  queries=qtitle if variant=='title' else qprofile
  targets=[' '.join(labs) for labs in labels]
  if variant=='title_context':targets=[t+' '+e['description'] for t,e in zip(targets,esco)]
  # Fit only ESCO target documents; test queries never alter the lexical vocabulary/IDF.
  vectorizer=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),lowercase=True,sublinear_tf=True,norm='l2',dtype=np.float32)
  mat=vectorizer.fit_transform(targets);lex=(vectorizer.transform(queries)@mat.T).toarray()
  emb=tn if variant=='title' else tp
  prof=tn if variant=='title' else tp
  def emit(method,i,js,scores,detail=None):
   for rank,j in enumerate(js,1):
    d=(detail or {}).get(j,{})
    candidates.append(dict(run_id=run,method=method,input_variant=variant,masco_version='2020',masco_code=roles[i]['code'],esco_version='1.2.1',esco_uri=esco[j]['concept_uri'],esco_code=esco[j]['code'],rank=rank,score=f'{float(scores[j]):.8f}',score_type='ranking_similarity_not_probability',title_cosine=f'{float(tn[i,j]):.8f}' if method!='lexical_tfidf' else '',profile_cosine=f'{float(prof[i,j]):.8f}' if method!='lexical_tfidf' else '',lexical_component=d.get('lexical',''),matched_label=d.get('label',''),label_boost=d.get('boost',''),candidate_origin='fresh_retrieval',review_status='unreviewed'))
  for i,r in enumerate(roles):
   emit('lexical_tfidf',i,ranked(lex[i],range(len(esco)),a.k),lex[i])
   emit('minilm',i,ranked(emb[i],range(len(esco)),a.k),emb[i])
   nt=norm(qtitle[i]);idx=set(ranked(tn[i],range(len(esco)),30))|set(ranked(prof[i],range(len(esco)),20))
   exact=exact_index[nt]
   idx|=exact; scores={};detail={}
   for j in idx:
    best=max(range(len(labels[j])),key=lambda z:SequenceMatcher(None,nt,normalized_labels[j][z]).ratio())
    label=labels[j][best]
    lexical=SequenceMatcher(None,nt,normalized_labels[j][best]).ratio();score=.65*float(tn[i,j])+.20*float(prof[i,j])+.15*lexical;boost='none'
    if nt==norm(etitle[j]):score=max(score,.995);boost='preferred_floor_0.995'
    elif j in exact:score=max(score,.985);boost='alternate_floor_0.985'
    scores[j]=score;detail[j]={'lexical':f'{lexical:.8f}','label':label,'boost':boost}
   emit('weighted_minilm_adaptation',i,ranked(scores,idx,a.k),scores,detail)
   if (i+1)%1000==0:print(variant,'retrieved',i+1,flush=True)
 write_csv(outdir/'candidates.csv',candidates,pairfields)
 from collections import Counter
 counts=Counter((r['method'],r['input_variant'],r['masco_code']) for r in candidates)
 assert len(counts)==len(roles)*6 and set(counts.values())=={a.k}
 for group in set(r['major_group'] for r in roles):assert any(r['major_group']==group for r in roles)
 # No scores are converted to accepted mappings. Pilot decisions remain separate.
 metadata={'run_id':run,'scope':a.scope,'seed':seed,'query_count':len(roles),'target_count':len(esco),'candidate_rows':len(candidates),'k':a.k,'model_id':'sentence-transformers/all-MiniLM-L6-v2','model_revision':REV,'device':'cpu','model_max_seq_length':model.max_seq_length,'normalize_embeddings':True,'batch_size':64,'torch_threads':4,'lexical':{'analyzer':'char_wb','ngram_range':[3,5],'sublinear_tf':True,'fit_corpus':'ESCO only','alternative_labels':True},'weighted_comparison':'0.65 title cosine + 0.20 profile cosine + 0.15 best-label SequenceMatcher; exact preferred/alternate floors .995/.985; top30 title union top20 profile union exact labels; no inherited pair injection','weighted_vs_pilot_difference':'MASCO publication unit-group descriptions replace inherited portal profiles; targets use preferred title + description; no inherited pair in pool, no manual decisions. Adaptation, not exact historical replay.','title_context':'MASCO title + explicitly qualified unit-group description; ESCO preferred title + description; tasks retained in source table but not used in this baseline','title_cleaning':'pilot clean_title removes Grade suffix and Competent Person (CP) prefix; original preserved','title_context_truncated_queries':sum(r['profile_truncated'] for r in inputs),'target_profile_truncated':sum(len(model.tokenizer.encode(t))>model.max_seq_length for t in eprofile),'score_is_probability':False,'independent_human_validation':False,'numeric_hierarchy_used':False,'elapsed_seconds':round(time.time()-start,2),'python':platform.python_version(),'dependencies':{n:importlib.metadata.version(n) for n in ['numpy','scikit-learn','sentence-transformers','torch','transformers','tokenizers','huggingface-hub','safetensors']},'inputs':{str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'data/processed/masco_occupations.csv',ROOT/'data/processed/masco_group_context.csv',ROOT/'data/processed/esco_occupations.csv']},'script_sha256':sha(Path(__file__)), 'candidate_sha256':sha(outdir/'candidates.csv'),'structural_smoke_checks_passed':True}
 save(outdir/'run.json',metadata);print(json.dumps(metadata,indent=2))
if __name__=='__main__':main()
