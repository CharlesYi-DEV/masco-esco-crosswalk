from common import *
from collections import Counter,defaultdict
import re
p=ROOT/'data/processed';occ=read_csv(p/'masco_occupations.csv');groups=read_csv(p/'masco_groups.csv');ctx=read_csv(p/'masco_group_context.csv');indices=read_csv(p/'masco_index_occurrences.csv')
checks={}
checks['occupation_codes_unique']=len({r['code'] for r in occ})==len(occ)
checks['codes_are_strings_and_valid']=all(re.fullmatch(r'\d{4}-\d{2}',r['code']) for r in occ)
checks['leading_zero_roles_preserved']=sum(r['code'].startswith('0') for r in occ)==145
checks['all_ten_major_groups']=set(r['major_group'] for r in occ)==set('0123456789')
checks['no_empty_titles']=all(r['title_original'] for r in occ)
gc={r['code'] for r in groups};cc={r['code'] for r in ctx}
checks['all_parents_exist']=all(not r['parent_code'] or r['parent_code'] in gc for r in occ+groups)
checks['all_groups_have_context']=gc==cc
checks['individual_context_not_fabricated']=all(not r['individual_description'] and not r['individual_tasks'] and r['context_scope']=='unit_group' for r in occ)
checks['all_unit_descriptions_and_tasks_present']=all(r['description'] and r['tasks'] for r in ctx if len(r['code'])==4)
# Independent first-column regex scan of each visible systematic row; parser uses column slicing.
pagecodes=[]
for line in (ROOT/'data/interim/pages.jsonl').read_text().splitlines():
 page=json.loads(line)
 if 316<=page['pdf_page']<=445:
  for r in page['rows']:
   m=re.match(r'^(\d{4}-\d{2})\s',r['text'])
   if m:pagecodes.append(m[1])
checks['independent_visible_row_code_scan_agrees']=Counter(pagecodes)==Counter(r['code'] for r in occ)
source_hash=sha(ROOT/'sources/raw/masco_2020_en.pdf')
checks['source_checksum_current']=all(r['source_sha256']==source_hash for r in occ+groups)
checks['no_false_nec_exclusion']=bool(next(r for r in ctx if r['code']=='2619')['description'])
# Historical private-workspace comparisons are outside this portable check.
prior={}
titles=defaultdict(list)
for r in occ:titles[r['title_original']].append(r['code'])
write_csv(ROOT/'review/repeated_titles.csv',[dict(title_original=t,codes_json=json.dumps(cs),count=len(cs)) for t,cs in titles.items() if len(cs)>1],['title_original','codes_json','count'])
gaps=[]
for g in groups:
 if len(g['code'])==4:
  suffixes={int(r['code'][-2:]) for r in occ if r['parent_code']==g['code']}
  for n in sorted(set(range(1,max(suffixes,default=0)+1))-suffixes):gaps.append(dict(unit_code=g['code'],absent_code=f'{g["code"]}-{n:02d}',interpretation='sequence gap only; not evidence that an occupation exists'))
write_csv(ROOT/'review/code_sequence_gaps.csv',gaps,['unit_code','absent_code','interpretation'])
report={'checks':checks,'passed':all(checks.values()),'unique_title_strings':len(titles),'repeated_title_strings':sum(len(c)>1 for c in titles.values()),'code_sequence_gaps':len(gaps),'prior_extraction_comparison':prior,'limits':'Structural and extraction consistency checks; not accuracy or completeness proof; no human review.'}
save(ROOT/'outputs/structural_checks.json',report);print(json.dumps(report,indent=2));assert report['passed']
