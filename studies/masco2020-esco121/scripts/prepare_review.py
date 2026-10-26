"""Prepare independent blank worksheets; AI never fills human decision fields."""
from common import *
import random,re,collections
rng=random.Random(20261026)
roles=read_csv(ROOT/'data/processed/masco_occupations.csv');contexts={r['code']:r for r in read_csv(ROOT/'data/processed/masco_group_context.csv')};esco={r['concept_uri']:r for r in read_csv(ROOT/'data/processed/esco_occupations.csv')}
# Group identical normalized titles into connected unit components solely to prevent
# label leakage. This does not assert that homonymous occupations have equal scope.
import unicodedata
units=sorted({r['parent_code'] for r in roles});parent={u:u for u in units}
def find(u):
 while parent[u]!=u:parent[u]=parent[parent[u]];u=parent[u]
 return u
def union(a,b):parent[find(a)]=find(b)
bytitle=collections.defaultdict(list)
for r in roles:
 key=' '.join(re.findall(r'\w+',unicodedata.normalize('NFKC',r['title_original']).casefold()))
 bytitle[key].append(r['parent_code'])
for us in bytitle.values():
 for u in us[1:]:union(us[0],u)
components=collections.defaultdict(list)
for u in units:components[find(u)].append(u)
components=sorted(components.values());split_rng=random.Random(20261026)
best=None
for trial in range(1000):
 dev={u for component in components if split_rng.random()<.2 for u in component}
 counts={g:(sum(r['major_group']==g and r['parent_code'] in dev for r in roles),sum(r['major_group']==g and r['parent_code'] not in dev for r in roles)) for g in '0123456789'}
 if any(d<3 or t<30 for d,t in counts.values()):continue
 penalty=sum(abs(sum(u[0]==g and u in dev for u in units)/sum(u[0]==g for u in units)-.2) for g in '0123456789')
 if best is None or penalty<best[0]:best=(penalty,dev)
assert best is not None,'No feasible partition; revise sample sizes explicitly'
dev=best[1];unit_split={u:('development' if u in dev else 'held_out') for u in units};sample=[]
for major in '0123456789':
 pop=[r for r in roles if r['major_group']==major]
 d=[r for r in pop if r['parent_code'] in dev];test=[r for r in pop if r['parent_code'] not in dev]
 for r in rng.sample(d,min(3,len(d))):sample.append((r,'calibration',len(d),''))
 chosen=rng.sample(test,min(20,len(test)));selected={r['code'] for r in chosen}
 for r in chosen:sample.append((r,'probability_test',len(test),len(chosen)/len(test)))
 challenge=[]
 for r in test:
  if r['code'] in selected:continue
  title=r['title_original'];flags=[]
  if len(contexts[r['parent_code']]['description'])<180:flags.append('sparse_group_context')
  if len(title.split())<=2 or re.search(r'\b(officer|executive|assistant|worker)\b',title,re.I):flags.append('ambiguous_or_short_title')
  if major=='0' or re.search(r'\b(grade|syariah|imam|penghulu|menteri|adiguru|islam|demang)\b',title,re.I):flags.append('national_or_institutional_scope')
  challenge.append((len(flags),rng.random(),r,';'.join(flags) or 'scope_comparison'))
 challenge.sort(key=lambda x:(-x[0],x[1]))
 for _,_,r,flag in challenge[:10]:sample.append((r,'challenge_test',len(test),flag))
fields=['decision_id','masco_version','masco_code','esco_version','esco_uri','relation','review_stage','decision_method','guide_version','reviewer_id','reviewer_type','reviewed_at','independence_attested','source_evidence','target_evidence','rationale','search_beyond_shortlist','search_terms_and_scope','minutes_spent','reference_completeness','review_status']
# Empty schema templates never overwritten if a person has started filling them.
def new_csv(path,rows,fields=None):
 if path.exists():raise FileExistsError(f'Refusing to overwrite review work: {path}')
 write_csv(path,rows,fields)
new_csv(ROOT/'review/decisions.csv',[],fields)
new_csv(ROOT/'review/accepted_mappings.csv',[],['mapping_id','masco_version','masco_code','esco_version','esco_uri','relation','adjudication_decision_id','supporting_decision_ids','source_evidence','target_evidence','rationale','accepted_by','accepted_at','status'])
new_csv(ROOT/'review/occupation_status.csv',[dict(masco_version='2020',masco_code=r['code'],status='unresolved',search_status='not_reviewed',reviewer_id='',reviewer_type='',reviewed_at='',evidence='',rationale='') for r in roles])
new_csv(ROOT/'review/reference_pairs.csv',[],['masco_code','esco_uri','relation','acceptable','reference_completeness','independent_human_reference','adjudication_id'])
new_csv(ROOT/'review/precision_audit.csv',[],['mapping_id','correct','auditor_id','independent_human_audit','evidence'])
new_csv(ROOT/'review/split_merge_evidence.csv',[],['change_type','old_codes_json','new_codes_json','evidence'])
new_csv(ROOT/'review/unit_partition.csv',[dict(unit_code=u,partition=s,seed=20261026) for u,s in sorted(unit_split.items())])
samplerows=[]
for r,cohort,n,x in sample:
 samplerows.append(dict(masco_code=r['code'],major_group=r['major_group'],unit_code=r['parent_code'],title=r['title_original'],cohort=cohort,partition=unit_split[r['parent_code']],eligible_major_population=n,inclusion_probability_conditional_on_partition=x if cohort=='probability_test' else '',challenge_flags=x if cohort=='challenge_test' else '',source_pdf_page=r['pdf_page'],title_pdf_page=r['title_pdf_page'],unit_context_pdf_page=contexts[r['parent_code']]['pdf_page_start']))
new_csv(ROOT/'review/sample.csv',samplerows)
for reviewer in ['R1','R2']:
 rows=[dict(**r,reviewer_id='',reviewer_type='human',occupation_status='',reference_completeness='',search_terms_and_scope='',extra_esco_uris='',minutes_spent='',notes='') for r in samplerows]
 new_csv(ROOT/f'review/{reviewer}_occupation_worksheet.csv',rows)
 new_csv(ROOT/f'review/{reviewer}_pair_decisions.csv',[],fields)
# Blinded union: no scores, rank, pilot labels or method shown to reviewers.
samplecodes={r['masco_code'] for r in samplerows};pool=collections.defaultdict(set)
for r in read_csv(ROOT/'outputs/full_20261026_k10/candidates.csv'):
 if r['masco_code'] in samplecodes:pool[r['masco_code']].add(r['esco_uri'])
poolrows=[]
for code,uris in sorted(pool.items()):
 uris=sorted(uris);rng.shuffle(uris)
 for j,uri in enumerate(uris,1):
  e=esco[uri];poolrows.append(dict(masco_code=code,display_order=j,esco_uri=uri,esco_code=e['code'],esco_title=e['title_original'],esco_description=e['description'],origin='pooled_fresh_candidate_unreviewed'))
new_csv(ROOT/'review/blinded_candidate_pool.csv',poolrows)
save(ROOT/'outputs/review_preparation.json',{'sample_size':len(sample),'cohorts':dict(collections.Counter(x[1] for x in sample)),'blinded_candidate_pairs':len(poolrows),'seed':20261026,'completed_human_reviews':0,'accepted_mappings':0,'held_out_policy':'entire MASCO unit groups and connected identical-normalized-title components assigned together before human labels; approximate 20% development units chosen from 1000 seeded feasible partitions; challenge cases are not probability sample','warning':'CSV templates are machine-readable; import all codes as text. Do not open and save through automatic numeric type inference.'})
print('Review sample',len(sample),'pooled pairs',len(poolrows))
