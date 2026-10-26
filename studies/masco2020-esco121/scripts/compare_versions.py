"""Same-schema inventory comparison; split/merge claims require supplied evidence.
Does not invent semantic change from numeric prefixes or title similarity.
"""
import argparse,json
from common import *
p=argparse.ArgumentParser();p.add_argument('old',type=Path);p.add_argument('new',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--evidence',type=Path);a=p.parse_args()
old={r['code']:r for r in read_csv(a.old)};new={r['code']:r for r in read_csv(a.new)};events=[]
old_hash,new_hash=sha(a.old),sha(a.new)
for code in sorted(old.keys()|new.keys()):
 before,after=old.get(code),new.get(code)
 changes=[]
 if before is None:changes=['addition']
 elif after is None:changes=['removal']
 else:
  if before.get('title_original')!=after.get('title_original'):changes.append('title_change')
  if any(before.get(k,'')!=after.get(k,'') for k in ['description','tasks','individual_description','individual_tasks']):changes.append('description_change')
  if before.get('parent_code')!=after.get('parent_code'):changes.append('parent_change')
 for change in changes:events.append(dict(change_type=change,old_codes_json=json.dumps([code] if before else []),new_codes_json=json.dumps([code] if after else []),evidence=json.dumps({'old_file_sha256':old_hash,'new_file_sha256':new_hash,'old_record':before,'new_record':after}),status='mechanical_difference_requires_semantic_review'))
if a.evidence:
 for r in read_csv(a.evidence):
  assert r['change_type'] in ['split','merge'] and r['evidence'].strip()
  oc,nc=json.loads(r['old_codes_json']),json.loads(r['new_codes_json'])
  assert set(oc)<=old.keys() and set(nc)<=new.keys()
  assert (len(oc)==1 and len(nc)>1) if r['change_type']=='split' else (len(oc)>1 and len(nc)==1)
  events.append(dict(change_type=r['change_type'],old_codes_json=json.dumps(oc),new_codes_json=json.dumps(nc),evidence=r['evidence'],status='evidence_supplied_requires_review'))
write_csv(a.out,events,['change_type','old_codes_json','new_codes_json','evidence','status']);print(len(events),'changes')
