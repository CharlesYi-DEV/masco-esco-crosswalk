"""Recover missing frozen sources without silently replacing existing bytes."""
import argparse,urllib.request,shutil,zipfile
from common import *
p=argparse.ArgumentParser();p.add_argument('--esco-zip',type=Path,help='Previously obtained official v1.2.1 English CSV archive');a=p.parse_args()
m=json.loads((ROOT/'sources/source_manifest.json').read_text())
for s in m['sources']:
 for f in s['files']:
  dest=ROOT/f['path']
  if dest.exists():assert sha(dest)==f['sha256'],f['path'];continue
  dest.parent.mkdir(parents=True,exist_ok=True);tmp=dest.with_suffix(dest.suffix+'.part')
  if s['source_id']=='masco2020_en':
   with urllib.request.urlopen(s['source_url'],timeout=120) as response,tmp.open('wb') as out:shutil.copyfileobj(response,out)
  elif dest.name=='esco_v1.2.1_en_csv.zip' and a.esco_zip:shutil.copyfile(a.esco_zip,tmp)
  elif dest.name=='occupations_en.csv':
   with zipfile.ZipFile(ROOT/'sources/raw/esco_v1.2.1_en_csv.zip') as z:tmp.write_bytes(z.read('occupations_en.csv'))
  else:print('Restore manually from frozen archive:',f['path']);continue
  assert sha(tmp)==f['sha256'],f'Checksum mismatch: {tmp}; inspect as new source, never overwrite frozen source'
  tmp.rename(dest)
