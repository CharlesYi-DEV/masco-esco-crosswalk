from common import *
from collections import defaultdict
p=ROOT/'sources/raw/esco_v1.2.1/occupations_en.csv';rows=read_csv(p);by=defaultdict(list)
for i,r in enumerate(rows,2):by[r['conceptUri']].append((i,r))
out=[];dupes=[]
for uri,rs in sorted(by.items()):
 chosen=sorted(rs,key=lambda x:(x[1]['modifiedDate'],x[0]))[-1]
 if len(rs)>1:
  for i,r in rs:dupes.append(dict(concept_uri=uri,csv_record_number=i,modified_date=r['modifiedDate'],selected=i==chosen[0],raw_record_json=json.dumps(r,ensure_ascii=False)))
 i,r=chosen
 out.append(dict(source_id='esco_v1.2.1_en',source_version='1.2.1',source_sha256=sha(p),concept_uri=uri,code=r['code'],title_original=r['preferredLabel'],alt_labels=r['altLabels'],description=r['description'],isco_group=r['iscoGroup'],language='en',csv_record_number=i,modified_date=r['modifiedDate']))
out.sort(key=lambda r:r['code'])
assert len({r['code'] for r in out})==len(out)
write_csv(ROOT/'data/processed/esco_occupations.csv',out)
write_csv(ROOT/'review/esco_duplicate_records.csv',dupes)
save(ROOT/'outputs/esco_import.json',{'raw_rows':len(rows),'unique_uris':len(out),'duplicate_uri_groups':sum(len(v)>1 for v in by.values()),'selection':'latest modifiedDate, then last CSV logical record; all alternatives retained for review','source_sha256':sha(p),'release_provenance':'existing official-release ZIP, original download timestamp unknown; not freshly downloaded'})
print(len(rows),len(out),len(dupes))
