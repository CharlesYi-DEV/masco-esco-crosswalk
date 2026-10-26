"""Version-specific MASCO 2020 parser. All pages are 1-based physical PDF pages.
Reads cached visible text, keeps alternative evidence rather than forcing published counts.
"""
import collections, json, re, unicodedata
from common import *
PDF=ROOT/'sources/raw/masco_2020_en.pdf'; H=sha(PDF)
pages=[json.loads(l) for l in (ROOT/'data/interim/pages.jsonl').read_text().splitlines()]
assert len(pages)==602
CODE=re.compile(r'^\d{4}-\d{2}$')
HEAD=re.compile(r'^(SUB[- ]MAJOR(?: GROUPS?)?|MINOR GROUPS?|UNIT GROUPS?)\s+(\d{2,4})\s+(.+)$', re.I)
PLAIN=re.compile(r'^(\d{2,4})\s+([A-Z].+)$')
issues=[]
def issue(kind,code,evidence,detail): issues.append(dict(issue_type=kind,code=code,evidence=evidence,detail=detail,review_status='unreviewed'))
def body(p):
 return [r for r in p['rows'] if 45<r['top']<805 and not r['text'].startswith('MALAYSIA STANDARD') and not re.fullmatch(r'\d+',r['text'])]
def norm(s): return re.sub(r'[^a-z0-9]','',unicodedata.normalize('NFKD',s).lower())
def ev(p,r):return f'PDF p.{p}, y={r["top"]:.2f}'
def occurrence(section,p,r,code,title,old=''):
 return dict(source_id='masco2020_en',source_sha256=H,section=section,code=code,title_original=title,language='en',pdf_page=p,printed_page=str(p-14),y_top=round(r['top'],2),masco2013_code_or_status=old)
occ=[];heads=[]
for p in pages:
 n=p['pdf_page'];rows=body(p)
 if 316<=n<=445 or 448<=n<=561:
  section='systematic_index' if n<=445 else 'alphabetical_index'
  prev=None
  for r in rows:
   words=r['words']; split=215 if section=='systematic_index' else 200
   code=' '.join(w['text'] for w in words if 70<=w['x0']<140)
   old=' '.join(w['text'] for w in words if 140<=w['x0']<split)
   title=' '.join(w['text'] for w in words if split<=w['x0']<580)
   if CODE.fullmatch(code):
    prev=occurrence(section,n,r,code,title,old);occ.append(prev)
   elif section=='systematic_index' and re.fullmatch(r'\d{1,4}',code) and title:
    heads.append(occurrence(section,n,r,code,title));prev=None
   elif not code and not old and title and prev and not re.fullmatch('[A-Z]',title) and title!='JOB TITLE':
    prev['title_original']+=' '+title
    issue('wrapped_title',prev['code'],ev(n,r),'Continuation joined to prior visible occupation row; verify line wrapping.')
   else: prev=None
 if 15<=n<=314:
  for j,r in enumerate(rows):
   m=HEAD.match(r['text']); q=PLAIN.match(r['text'])
   if m:
    code,title=m[2],m[3] or '';kind='narrative_heading'
   elif q and q[2].upper()==q[2]: code,title=q[1],q[2];kind='classification_list'
   else:continue
   # Only a nearby unnumbered uppercase continuation belongs to this heading.
   for nxt in rows[j+1:j+4]:
    t=nxt['text']
    if t and t.upper()==t and re.search('[A-Z]',t) and not re.match(r'^(\d|SUB|MINOR|UNIT|MAJOR|MASCO|GROUP|Description|Skills)',t) and nxt['top']-r['top']<55: title+=' '+t
    else:break
   heads.append(occurrence(kind,n,r,code,title.strip()))
# Group-level narratives: stop at next explicit heading or chapter boundary.
# Each raw block retains page markers, descriptions/tasks/examples/exclusions are separate.
blocks=[];current=None
for p in pages[14:314]:
 n=p['pdf_page'];rows=body(p)
 for r in rows:
  m=HEAD.match(r['text'])
  if m:
   if current:blocks.append(current)
   current={'code':m[2],'title':m[3] or '', 'start_page':n,'start_y':r['top'],'lines':[]}
  elif current:
   current['lines'].append((n,r['text']))
 # End chapter before decorative/summary pages of next major group.
 if n in [40,114,166,184,208,222,258,282,302,314] and current:
  blocks.append(current);current=None
if current: blocks.append(current)
contexts={}
# Explicit major narrative page locations, checked against chapter openings.
for code,n in [('1',19),('2',49),('3',121),('4',171),('5',189),('6',213),('7',229),('8',263),('9',287),('0',307)]:
 rows=body(pages[n-1]); lines=[]; started=False
 for r in rows:
  t=r['text']
  if t.startswith('Occupations in this major group'):break
  if not started and (t.upper()==t or t=='Craft and Related Trades Workers'):continue
  started=True; lines.append(t)
 contexts[code]=dict(code=code,source_id='masco2020_en',source_sha256=H,context_scope='major_group',pdf_page_start=n,pdf_page_end=n,y_start=rows[0]['top'],description='\n'.join(lines),tasks='',inclusions='',exclusions='',other='',raw_block='\n'.join(f'[PDF p.{n}] {t}' for t in lines),review_status='machine_extracted_unreviewed')
for b in blocks:
 lines=list(b['lines'])
 while lines and lines[0][1].upper()==lines[0][1] and re.search('[A-Z]',lines[0][1]):lines.pop(0)
 sections={'description':[],'tasks':[],'inclusions':[],'exclusions':[],'other':[]};part='description'
 for n,t in lines:
  if re.match(r'^(T\s?asks? include|Tugas merangkumi)' ,t,re.I):part='tasks';continue
  if re.match(r'^(Examples? of|Occupations (in|classified))',t,re.I):part='inclusions'
  if re.search(r'^(Some related occupations|Occupations.*classified elsewhere|Excluded occupations|Exclusions)',t,re.I):part='exclusions'
  # After examples and notes, never let a new chapter/list leak into model input.
  sections[part].append(t)
 c=dict(code=b['code'],source_id='masco2020_en',source_sha256=H,context_scope={2:'sub_major_group',3:'minor_group',4:'unit_group'}[len(b['code'])],pdf_page_start=b['start_page'],pdf_page_end=max([b['start_page']]+[n for n,t in lines]),y_start=round(b['start_y'],2),
        **{k:'\n'.join(v) for k,v in sections.items()},raw_block='\n'.join(f'[PDF p.{n}] {t}' for n,t in b['lines']),review_status='machine_extracted_unreviewed')
 if b['code'] in contexts:issue('duplicate_narrative_heading',b['code'],str(b['start_page']),'Multiple narrative blocks; first retained; raw heading occurrences preserved.')
 else:contexts[b['code']]=c
# Prefer systematic index labels; then narrative headings; then chapter lists.
byhead=collections.defaultdict(list)
for h in heads:byhead[h['code']].append(h)
groups=[]
for code, hs in sorted(byhead.items()):
 if len(code) not in [1,2,3,4]:continue
 hs.sort(key=lambda x:({'systematic_index':0,'narrative_heading':1,'classification_list':2}[x['section']],x['pdf_page']))
 h=hs[0];c=contexts.get(code)
 groups.append(dict(source_id='masco2020_en',source_version='2020',source_sha256=H,code=code,level={1:'major',2:'sub_major',3:'minor',4:'unit'}[len(code)],parent_code=code[:-1],title_original=h['title_original'],language='en',pdf_page=h['pdf_page'],y_top=h['y_top'],title_evidence_section=h['section'],context_available=bool(c),context_scope=c['context_scope'] if c else '',review_status='machine_extracted_unreviewed'))
 if not c:issue('no_parsed_group_context',code,ev(h['pdf_page'],{'top':h['y_top']}),'No explicit narrative block parsed; do not infer individual description.')
 # Uppercase spelling differences remain evidence, never silent repairs.
 variants={norm(x['title_original']) for x in hs}
 if len(variants)>1:issue('group_title_variants',code,','.join(str(x['pdf_page']) for x in hs),json.dumps(sorted({x['title_original'] for x in hs}),ensure_ascii=False))
sys=collections.defaultdict(list);alpha=collections.defaultdict(list)
for r in occ:(sys if r['section']=='systematic_index' else alpha)[r['code']].append(r)
records=[]
for code,rs in sorted(sys.items()):
 r=rs[0];a=alpha.get(code,[]);titles={norm(x['title_original']) for x in a}
 if len(rs)>1:issue('duplicate_systematic_code',code,str([x['pdf_page'] for x in rs]),'Repeated code retained in occurrences; canonical row uses first systematic entry.')
 if not a:issue('missing_alphabetical_code',code,str(r['pdf_page']),'No visible alphabetical row found.')
 elif norm(r['title_original']) not in titles:issue('index_title_disagreement',code,str(r['pdf_page']),json.dumps({'systematic':r['title_original'],'alphabetical':[x['title_original'] for x in a]},ensure_ascii=False))
 title=r['title_original'];title_ev=r
 if not title:
  issue('systematic_title_text_missing',code,str(r['pdf_page']),'Visible systematic title absent from parsed text; use unique alphabetical title, corroborated by assistant visual inspection on 2026-10-26; requires human review.')
  if len({x['title_original'] for x in a})==1: title=a[0]['title_original'];title_ev=a[0]
  else:issue('missing_title',code,str(r['pdf_page']),'No unique alternate title evidence.')
 records.append(dict(source_id='masco2020_en',source_version='2020',source_sha256=H,code=code,code_digits=code.replace('-',''),parent_code=code[:4],major_group=code[0],title_original=title,title_evidence_section=title_ev['section'],title_pdf_page=title_ev['pdf_page'],title_y_top=title_ev['y_top'],language='en',pdf_page=r['pdf_page'],printed_page=r['printed_page'],y_top=r['y_top'],individual_description='',individual_tasks='',context_code=code[:4] if code[:4] in contexts else '',context_scope='unit_group' if code[:4] in contexts else '',alphabetical_occurrences=len(a),extraction_status='machine_extracted_unreviewed'))
for code,rs in alpha.items():
 if code not in sys:issue('alphabetical_only_code',code,str([x['pdf_page'] for x in rs]),json.dumps([x['title_original'] for x in rs]))
gcodes={g['code'] for g in groups}
for r in records+groups:
 if r['parent_code'] and r['parent_code'] not in gcodes:issue('missing_parent',r['code'],str(r['pdf_page']),r['parent_code'])
# Reconcile table on physical p.11 independently of its contradictory paragraph.
published={'1':[6,11,38,551],'2':[9,37,123,2171],'3':[7,23,90,1211],'4':[4,8,28,372],'5':[4,13,41,317],'6':[3,9,19,213],'7':[6,14,67,672],'8':[3,15,42,713],'9':[6,11,35,265],'0':[3,6,7,145]}
counts=[]
for major in sorted(published):
 for idx,level in enumerate(['sub_major','minor','unit','occupation']):
  actual=sum(r['major_group']==major for r in records) if level=='occupation' else sum(g['code'][0]==major and g['level']==level for g in groups)
  counts.append(dict(major_group=major,level=level,extracted_unique=actual,published_table=published[major][idx],difference=actual-published[major][idx],source_pdf_page=11))
write_csv(ROOT/'data/processed/masco_groups.csv',groups)
write_csv(ROOT/'data/processed/masco_occupations.csv',records)
write_csv(ROOT/'data/processed/masco_index_occurrences.csv',occ)
write_csv(ROOT/'data/processed/masco_heading_occurrences.csv',heads)
write_csv(ROOT/'data/processed/masco_group_context.csv',list(contexts.values()))
write_csv(ROOT/'review/extraction_queue.csv',issues)
write_csv(ROOT/'outputs/count_reconciliation.csv',counts)
report={'pdf_pages':len(pages),'source_sha256':H,'counts_by_level':dict(collections.Counter(g['level'] for g in groups)),'unique_occupation_codes':len(records),'systematic_rows':sum(map(len,sys.values())),'alphabetical_rows':sum(map(len,alpha.values())),'alphabetical_unique_codes':len(alpha),'alphabetical_only_codes':sorted(set(alpha)-set(sys)),'systematic_only_codes':sorted(set(sys)-set(alpha)),'group_context_blocks':len(contexts),'issues_by_type':dict(collections.Counter(x['issue_type'] for x in issues)),'published_table_totals':{'major':10,'sub_major':51,'minor':147,'unit':490,'occupation_titles':6630},'published_prose_totals':{'minor':146,'unit':490,'occupation_titles':6366},'human_validation_performed':False}
save(ROOT/'outputs/extraction_quality.json',report);print(json.dumps(report,indent=2))
