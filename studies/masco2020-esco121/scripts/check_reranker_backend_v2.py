"""Numerical/backend validation only, not occupation accuracy evaluation."""
import json,time
import numpy as np
from common import ROOT,read_csv,save,sha
from hybrid_v2 import canonical_inputs
from rerank_v2 import QwenScorer
from mlx_reranker_v2 import MLXQwenScorer

lock=json.loads((ROOT/'sources/models_v2.lock.json').read_text())['qwen_reranker']
roles=read_csv(ROOT/'data/processed/masco_occupations.csv')[:4]
esco=read_csv(ROOT/'data/processed/esco_occupations.csv')[:8]
ctx={r['code']:r for r in read_csv(ROOT/'data/processed/masco_group_context.csv')}
qs,ds=canonical_inputs(roles,esco,ctx,'title_context')
pairs=[(q,d) for q in qs for d in ds]
results={}
for key,cls in [('torch',QwenScorer),('mlx',MLXQwenScorer)]:
    model=cls(ROOT/lock['path'],'mps','bfloat16')
    model.predict(pairs[:2])
    start=time.time();values=model.predict(pairs)
    results[key]=dict(seconds=time.time()-start,scores=values.tolist())
    if key=='mlx':
        singles=[float(model.predict([pair])[0]) for pair in pairs[:4]]
        results[key]['batch_vs_single_max_abs_difference']=float(np.max(np.abs(np.array(singles)-values[:4])))
        repeated=[(qs[0],d) for d in ds]*4
        t=time.time();cached=model.predict(repeated)
        results[key]['cached_32_pair_seconds']=time.time()-t
        model.use_prefix_cache=False
        t=time.time();uncached=model.predict(repeated)
        results[key]['uncached_32_pair_seconds']=time.time()-t
        results[key]['cached_vs_uncached_max_abs_difference']=float(np.max(np.abs(cached-uncached)))
    del model
    import gc;gc.collect()
    import torch;torch.mps.empty_cache()
delta=np.max(np.abs(np.array(results['torch']['scores'])-results['mlx']['scores']))
results['backend_max_abs_logit_difference']=float(delta)
results['tolerance']=0.5
results['passed']=bool(delta<0.5 and results['mlx']['batch_vs_single_max_abs_difference']<0.5 and results['mlx']['cached_vs_uncached_max_abs_difference']<0.5)
results['script_sha256']=sha(__file__)
save(ROOT/'outputs/reranker_backend_check_v2.json',results)
print(json.dumps(results,indent=2))
if not results['passed']:raise SystemExit(1)
