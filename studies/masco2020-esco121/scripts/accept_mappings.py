"""Explicit human adjudication gate. No score threshold can accept a mapping."""
from common import *
if not __debug__: raise RuntimeError("Validation assertions require normal Python execution; -O is prohibited")
import argparse
ACCEPTABLE={'equivalent_scope','masco_narrower_than_esco','masco_broader_than_esco','close_overlap_without_containment'}
RELATIONS=ACCEPTABLE|{'related_insufficient','incorrect_candidate'}
def build(decisions,source_codes,target_uris):
 ids=[d['decision_id'] for d in decisions];assert len(ids)==len(set(ids)) and all(ids)
 accepted=[]
 for d in decisions:
  assert d['relation'] in RELATIONS and d['masco_version']=='2020' and d['esco_version']=='1.2.1'
  assert d['masco_code'] in source_codes and d['esco_uri'] in target_uris
  assert d['reviewer_type'] in {'human','ai'}
  assert d['review_stage'] in {'independent','adjudication','ai_proposal'}
  if d['review_stage']=='ai_proposal':continue
  assert d['reviewer_type']=='human' and d['reviewer_id'] and d['reviewed_at']
  assert d['source_evidence'] and d['target_evidence'] and d['rationale'] and d['review_status']=='completed'
  assert d['decision_method'] and d['guide_version'], 'Record review method and annotation guide version'
  if d['review_stage']!='adjudication' or d['relation'] not in ACCEPTABLE:continue
  support=[r for r in decisions if r['masco_code']==d['masco_code'] and r['esco_uri']==d['esco_uri'] and r['review_stage']=='independent' and r['reviewer_type']=='human' and r['review_status']=='completed' and r['independence_attested'].lower()=='true']
  reviewers={r['reviewer_id'] for r in support};assert len(reviewers)>=2,'Two independent human reviewers required'
  assert d['reviewer_id'] not in reviewers,'Separate adjudicator required by this protocol'
  accepted.append(dict(mapping_id='map_'+d['decision_id'],masco_version='2020',masco_code=d['masco_code'],esco_version='1.2.1',esco_uri=d['esco_uri'],relation=d['relation'],adjudication_decision_id=d['decision_id'],supporting_decision_ids=json.dumps([r['decision_id'] for r in support]),source_evidence=d['source_evidence'],target_evidence=d['target_evidence'],rationale=d['rationale'],accepted_by=d['reviewer_id'],accepted_at=d['reviewed_at'],status='human_adjudicated'))
 assert len({(r['masco_code'],r['esco_uri']) for r in accepted})==len(accepted),'Resolve superseded/conflicting adjudications before acceptance'
 return accepted
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('decisions',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 assert not a.out.exists(),'Use a new versioned accepted-mapping output; never overwrite'
 rows=build(read_csv(a.decisions),{r['code'] for r in read_csv(ROOT/'data/processed/masco_occupations.csv')},{r['concept_uri'] for r in read_csv(ROOT/'data/processed/esco_occupations.csv')})
 fields=list(rows[0]) if rows else ['mapping_id','masco_version','masco_code','esco_version','esco_uri','relation','adjudication_decision_id','supporting_decision_ids','source_evidence','target_evidence','rationale','accepted_by','accepted_at','status']
 write_csv(a.out,rows,fields);print(len(rows),'accepted mappings')
