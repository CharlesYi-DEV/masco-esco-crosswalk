"""Evaluate only explicitly supplied independent human reference pairs.
Partially judged pools yield judged-positive hit rates, not Recall@k.
"""
from common import *
if not __debug__: raise RuntimeError("Validation assertions require normal Python execution; -O is prohibited")
import argparse,collections
p=argparse.ArgumentParser();p.add_argument('--candidates',type=Path,required=True);p.add_argument('--reference',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
ref=read_csv(a.reference)
if not ref:raise SystemExit('No reference pairs: metrics are not estimable; no evaluation result written.')
assert all(r['independent_human_reference'].lower()=='true' and r['adjudication_id'] for r in ref),'AI/inherited references are prohibited'
assert all(r['reference_completeness'] in ['exhaustive','partial_pool'] for r in ref)
assert all(r['acceptable'].lower() in ['true','false'] for r in ref)
assert len({(r['masco_code'],r['esco_uri']) for r in ref})==len(ref)
by=collections.defaultdict(list)
for r in ref:by[r['masco_code']].append(r)
for rows in by.values():assert len({r['reference_completeness'] for r in rows})==1
cand=collections.defaultdict(list)
for r in read_csv(a.candidates):cand[(r['method'],r['input_variant'],r['masco_code'])].append(r)
results=[]
for method,variant in sorted({(x[0],x[1]) for x in cand}):
 for k in [1,5,10]:
  measures={'exhaustive':[],'partial_pool':[]};judged=correct=unjudged=0
  for code,refs in by.items():
   rows=sorted(cand.get((method,variant,code),[]),key=lambda r:int(r['rank']))
   assert len(rows)>=k,f'Missing top-{k} candidates for {code}'
   retrieved={r['esco_uri'] for r in rows[:k]};gold={r['esco_uri'] for r in refs if r['acceptable'].lower()=='true'}
   if gold:measures[refs[0]['reference_completeness']].append(len(gold&retrieved)/len(gold))
   judgedset={r['esco_uri'] for r in refs};judged+=len(retrieved&judgedset);correct+=len(retrieved&gold);unjudged+=len(retrieved-judgedset)
  results.append(dict(method=method,input_variant=variant,k=k,macro_recall_at_k=sum(measures['exhaustive'])/len(measures['exhaustive']) if measures['exhaustive'] else None,exhaustive_positive_sources=len(measures['exhaustive']),partial_pool_judged_positive_hit_rate=sum(measures['partial_pool'])/len(measures['partial_pool']) if measures['partial_pool'] else None,partial_positive_sources=len(measures['partial_pool']),judged_candidate_precision=correct/judged if judged else None,unjudged_candidate_count=unjudged,warning='Unweighted diagnostic; use preregistered sampling weights and unit-cluster bootstrap for publication. Candidate precision is not accepted-pair precision.'))
save(a.out,{'reference_sha256':sha(a.reference),'candidate_sha256':sha(a.candidates),'metrics':results})
