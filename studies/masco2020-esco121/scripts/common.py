from pathlib import Path
import csv, hashlib, json, os
ROOT=Path(os.environ.get('MASCO_ESCO_STUDY_ROOT', Path(__file__).resolve().parents[1])).expanduser().resolve()
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read_csv(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def write_csv(p, rows, fields=None):
 p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
 if fields is None: fields=list(rows[0]) if rows else []
 with p.open('w',encoding='utf-8',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
def save(p, obj):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
