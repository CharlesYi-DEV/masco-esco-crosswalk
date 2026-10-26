"""Structural validation and descriptive changes; never an accuracy estimate."""
import csv,json,math
from collections import defaultdict
from common import ROOT,read_csv,save,sha,write_csv

config=json.loads((ROOT/'configs/review_pool_v2.json').read_text())
roles={r['code']:r for r in read_csv(ROOT/'data/processed/masco_occupations.csv')}
uris={r['concept_uri'] for r in read_csv(ROOT/'data/processed/esco_occupations.csv')}
sample={r['masco_code'] for r in read_csv(ROOT/'review/sample.csv')}
summary=[];tops=defaultdict(lambda:defaultdict(list));lexical={}
for name in config['runs']:
    path=ROOT/'outputs'/name
    meta=json.loads((path/'run.json').read_text())
    if sha(path/'candidates.csv')!=meta['candidate_sha256']:raise ValueError('Changed candidates')
    counts=defaultdict(int);seen=set();last={};row_count=0
    with (path/'candidates.csv').open() as f:
        for r in csv.DictReader(f):
            code=r['masco_code'];uri=r['esco_uri'];rank=int(r['rank']);score=float(r['score'])
            key=(r['method'],r['input_variant'],code)
            if code not in roles or uri not in uris or not math.isfinite(score):raise ValueError('Invalid row')
            if rank!=counts[key]+1:raise ValueError('Ranks not contiguous')
            if key in last and score>last[key]+1e-8:raise ValueError('Scores not descending')
            pair=(*key,uri)
            if pair in seen:raise ValueError('Duplicate URI per query/method')
            seen.add(pair);last[key]=score;counts[key]+=1;row_count+=1
            if rank<=10 and code in sample:
                method=(r['method'],r['input_variant'])
                # Lexical channels are identical copies across encoder runs.
                if method in [('bm25','title_context'),('tfidf','title_context')]:
                    lkey=(*method,code,rank)
                    value=(uri,r['score'])
                    if lkey in lexical and lexical[lkey]!=value:raise ValueError('Lexical control differs across encoders')
                    lexical[lkey]=value
                if uri not in tops[method][code]:tops[method][code].append(uri)
    depth=10 if name=='full_20261026_k10' else 100
    if set(counts.values())!={depth}:raise ValueError('Wrong candidate depth')
    target_codes=sample if name=='v2_rerank_review' else set(roles)
    bymethod=defaultdict(set)
    for method,variant,code in counts:bymethod[(method,variant)].add(code)
    if any(codes!=target_codes for codes in bymethod.values()):raise ValueError('Wrong source coverage')
    summary.append(dict(run_id=name,queries=len(target_codes),rows=row_count,
        methods=len(bymethod),k=depth,elapsed_seconds=meta['elapsed_seconds'],candidate_sha256=sha(path/'candidates.csv')))
    del seen
comparison=[]
reference=tops[('hybrid_minilm','title_context')]
for (method,variant),percode in sorted(tops.items()):
    if variant!='title_context':continue
    shared=[];same=0
    for code in sorted(sample):
        a=reference[code];b=percode[code]
        shared.append(len(set(a)&set(b)))
        same+=a[0]==b[0]
    comparison.append(dict(method=method,variant=variant,comparison='v2 hybrid MiniLM',
        sources=len(sample),mean_shared_top10=sum(shared)/len(shared),same_top1_count=same,
        interpretation='Unlabelled agreement only; not accuracy or improvement'))
pool=ROOT/'review'/config['review_version']/'blinded_candidate_pool.csv'
poolrows=read_csv(pool)
if any(set(r)!={'pair_id','masco_code','display_order','esco_uri','esco_code','esco_title','esco_description'} for r in poolrows):
    raise ValueError('Blinding schema violated')
if len({r['pair_id'] for r in poolrows})!=len(poolrows):raise ValueError('Pair ID collision')
poolset={(r['masco_code'],r['esco_uri'],r['pair_id']) for r in poolrows}
for reviewer in ['R1','R2']:
    rows=read_csv(pool.parent/f'{reviewer}_candidate_pool.csv')
    if len(rows)!=len(poolrows) or {(r['masco_code'],r['esco_uri'],r['pair_id']) for r in rows}!=poolset:
        raise ValueError('Reviewers did not receive the same candidate set')
    if any(set(r)!=set(poolrows[0]) for r in rows):raise ValueError('Reviewer blinding schema differs')
for name in ['sample.csv','unit_partition.csv']:
    if sha(pool.parent/name)!=sha(ROOT/'review'/name):raise ValueError('Review sample or split changed')
write_csv(ROOT/'outputs/v2_run_summary.csv',summary)
write_csv(ROOT/'outputs/v2_unlabelled_agreement.csv',comparison)
save(ROOT/'outputs/v2_execution_audit.json',dict(status='passed',runs=summary,
    blinded_pairs=len(poolrows),review_sources=len(sample),methods=len(config['expected_methods']),
    original_decisions_rows=len(read_csv(ROOT/'review/decisions.csv')),
    original_accepted_rows=len(read_csv(ROOT/'review/accepted_mappings.csv')),
    equal_reviewer_candidate_sets=True,original_sample_and_partition_unchanged=True,
    measured_accuracy=None,measured_improvement=None))
print(json.dumps(dict(status='passed',runs=len(summary),blinded_pairs=len(poolrows),methods=len(config['expected_methods'])),indent=2))
