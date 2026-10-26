"""Extract only visible upright glyphs; retain coordinates and immutable page evidence.
Never use unfiltered PDF text: this publication includes text outside page boundaries.
"""
import json, re
import pdfplumber
from common import ROOT, sha, save
p=ROOT/'sources/raw/masco_2020_en.pdf'
out=ROOT/'data/interim/pages.jsonl'
out.parent.mkdir(parents=True,exist_ok=True)
with pdfplumber.open(p) as pdf, out.open('w') as f:
 for i,page in enumerate(pdf.pages):
  # Header/footer retained in cache; downstream parser applies section-specific bounds.
  chars=[]; seen=set(); hidden=0
  for c in page.chars:
   if not (0<=c['x0']<page.width and 0<c['top']<page.height and c['upright']): hidden+=1;continue
   key=(round(c['x0'],1),round(c['top'],1),c['text'])
   if key in seen: continue
   seen.add(key);chars.append(c)
  words=pdfplumber.utils.extract_words(chars,x_tolerance=1.2,y_tolerance=2)
  buckets=[]
  for w in sorted(words,key=lambda x:(x['top'],x['x0'])):
   row=next((r for r in reversed(buckets[-3:]) if abs(r['top']-w['top'])<2.5),None)
   if row is None: row={'top':w['top'],'words':[]};buckets.append(row)
   row['words'].append({k:w[k] for k in ['text','x0','x1','top','bottom']})
  for row in buckets:
   row['words'].sort(key=lambda x:x['x0']);row['text']=' '.join(w['text'] for w in row['words'])
  f.write(json.dumps({'pdf_page':i+1,'width':page.width,'height':page.height,'excluded_glyphs':hidden,'rows':buckets},ensure_ascii=False)+'\n')
  page.close()
  if (i+1)%50==0: print('Cached',i+1,flush=True)
save(ROOT/'data/interim/pdf_cache_metadata.json',{'source_sha256':sha(p),'pages':i+1,'pdfplumber_version':pdfplumber.__version__,'coordinates':'points, top-left origin','deduplication':'identical text at x/top rounded to 0.1pt','filter':'upright glyphs whose origin is within visible page'})
