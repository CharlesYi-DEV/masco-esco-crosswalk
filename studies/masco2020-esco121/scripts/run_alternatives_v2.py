"""Sequential GPU execution; skip only completed, previously frozen runs."""
import subprocess
import sys
from common import ROOT

for encoder,name in [('minilm','v2_minilm_full'),('gemma2','v2_gemma2_full'),('jina5_retrieval','v2_jina5_full')]:
    if (ROOT/'outputs'/name/'run.json').exists():
        continue
    print('Starting',name,flush=True)
    with (ROOT/'outputs'/f'{name}.log').open('w') as log:
        result=subprocess.run([sys.executable,str(ROOT/'scripts/hybrid_v2.py'),'--encoder',encoder,
            '--scope','full','--variants','title_context','--device','mps','--dtype','bfloat16',
            '--batch-size','32','--run-id',name],stdout=log,stderr=subprocess.STDOUT,cwd=ROOT)
    if result.returncode:
        print('Failed',name,'see log',flush=True)
        sys.exit(result.returncode)
    print('Completed',name,flush=True)
