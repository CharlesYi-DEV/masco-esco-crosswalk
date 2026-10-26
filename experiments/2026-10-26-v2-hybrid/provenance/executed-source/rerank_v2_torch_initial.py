"""Qwen3 reranking with pair reuse across controlled hybrid candidate pools."""
import argparse
import csv
import json
import sqlite3
import time
from collections import defaultdict
from common import ROOT, read_csv, save, sha
from hybrid_v2 import INSTRUCTION, fingerprint, canonical_inputs
import numpy as np

class QwenScorer:
    """Official Qwen yes/no prompt, avoiding CrossEncoder pair-template incompatibility."""
    def __init__(self,path,device,dtype):
        import torch
        from transformers import AutoTokenizer,AutoModelForCausalLM
        self.torch=torch
        self.tokenizer=AutoTokenizer.from_pretrained(str(path),local_files_only=True,padding_side='left')
        self.model=AutoModelForCausalLM.from_pretrained(str(path),local_files_only=True,
            dtype=getattr(torch,dtype)).to(device).eval()
        self.prefix=self.tokenizer.encode('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n',add_special_tokens=False)
        self.suffix=self.tokenizer.encode('<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n',add_special_tokens=False)
        self.yes=self.tokenizer.convert_tokens_to_ids('yes')
        self.no=self.tokenizer.convert_tokens_to_ids('no')
        if self.yes==self.no or self.yes==self.tokenizer.unk_token_id or self.no==self.tokenizer.unk_token_id:
            raise ValueError('Invalid yes/no token IDs')

    def predict(self,pairs,batch_size=16,show_progress_bar=False):
        texts=[f'<Instruct>: {INSTRUCTION}\n<Query>: {q}\n<Document>: {d}' for q,d in pairs]
        tokens=self.tokenizer(texts,padding=False,add_special_tokens=False)['input_ids']
        tokens=[self.prefix+t+self.suffix for t in tokens]
        if any(len(t)>2048 for t in tokens):
            raise ValueError('Refusing silent reranker truncation')
        inputs=self.tokenizer.pad({'input_ids':tokens},padding=True,return_tensors='pt').to(self.model.device)
        with self.torch.inference_mode():
            logits=self.model(**inputs,logits_to_keep=1,use_cache=False).logits[:,-1,:]
            return (logits[:,self.yes].float()-logits[:,self.no].float()).cpu().numpy()

def score_pairs(model, pairs, batch_size):
    scores = np.asarray(model.predict(pairs,batch_size=batch_size,show_progress_bar=False)).reshape(-1)
    if len(scores)!=len(pairs) or not np.isfinite(scores).all():
        raise ValueError('Invalid reranker scores')
    return [float(x) for x in scores]

def main(a):
    import torch
    torch.manual_seed(20261026)
    torch.set_num_threads(4)
    start=time.time()
    out=ROOT/'outputs'/a.run_id
    out.mkdir(exist_ok=True)
    if (out/'run.json').exists():
        raise FileExistsError('Completed rerank run is immutable')
    locks=json.loads((ROOT/'sources/models_v2.lock.json').read_text())
    record=locks['qwen_reranker']
    model=QwenScorer(ROOT/record['path'],a.device,a.dtype)
    tokenizer=model.tokenizer
    # Simple semantic smoke checks detect inverted yes/no polarity or broken prompt handling.
    sanity=score_pairs(model,[('Nurse','A registered nurse provides nursing care to patients.'),
                              ('Nurse','A bricklayer builds walls with bricks and mortar.')],2)
    if sanity[0]<=sanity[1]:
        raise ValueError(f'Reranker sanity check failed: {sanity}')
    roles=read_csv(ROOT/'data/processed/masco_occupations.csv')
    if a.scope!='full':
        sample=read_csv(ROOT/'review/sample.csv')
        codes={r['masco_code'] for r in sample if a.scope=='review' or r['cohort']=='calibration'}
        roles=[r for r in roles if r['code'] in codes]
    codes={r['code'] for r in roles}
    esco=sorted(read_csv(ROOT/'data/processed/esco_occupations.csv'),key=lambda e:e['concept_uri'])
    ctx={r['code']:r for r in read_csv(ROOT/'data/processed/masco_group_context.csv')}
    uri_index={e['concept_uri']:i for i,e in enumerate(esco)}
    groups=defaultdict(lambda:defaultdict(list))
    source_hashes={}
    for name in a.runs:
        path=ROOT/'outputs'/name/'candidates.csv'
        metadata=json.loads((path.parent/'run.json').read_text())
        if metadata['candidate_sha256']!=sha(path):
            raise ValueError('Candidate file changed')
        source_hashes[name]=sha(path)
        with path.open() as f:
            for r in csv.DictReader(f):
                if r['method'].startswith('hybrid_') and r['masco_code'] in codes:
                    groups[(r['masco_code'],r['input_variant'])][r['method']].append(r)
    variants=sorted({variant for _,variant in groups})
    texts={}
    for variant in variants:
        qs,ds=canonical_inputs(roles,esco,ctx,variant)
        texts[variant]=({r['code']:q for r,q in zip(roles,qs)},ds)
    token_bounds={variant:dict(query_max_tokens=max(len(tokenizer.encode(q)) for q in qs.values()),
        document_max_tokens=max(len(tokenizer.encode(d)) for d in ds)) for variant,(qs,ds) in texts.items()}
    # A deliberately conservative allowance covers the system, instruction and chat syntax.
    overhead=len(tokenizer.encode(INSTRUCTION))+256
    for bound in token_bounds.values():
        bound['conservative_pair_token_upper_bound']=bound['query_max_tokens']+bound['document_max_tokens']+overhead
        if bound['conservative_pair_token_upper_bound']>2048:
            raise ValueError('Possible pair truncation: inspect inputs before changing the frozen limit')
    config=dict(source_hashes=source_hashes,scope=a.scope,model=record,device=a.device,dtype=a.dtype,
        instruction=INSTRUCTION,max_length=2048,token_bounds=token_bounds,script_sha256=sha(__file__),batch_size=a.batch_size)
    configpath=out/'execution_config.json'
    if configpath.exists() and json.loads(configpath.read_text())!=config:
        raise ValueError('Cannot resume with changed config')
    save(configpath,config)
    cache=sqlite3.connect(ROOT/'data/interim/v2_reranker_cache.sqlite')
    cache.execute('CREATE TABLE IF NOT EXISTS scores (key TEXT PRIMARY KEY, score REAL NOT NULL)')
    namespace=fingerprint([record,INSTRUCTION,2048,a.dtype,a.device,sha(__file__)])
    temp=out/'candidates.incomplete.csv'
    fieldnames=['run_id','method','input_variant','masco_version','masco_code','esco_version','esco_uri',
        'rank','score','score_type','hybrid_rank','candidate_origin','review_status']
    count=0;computed=0;reused=0
    expected_methods=None
    with temp.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader()
        for n,((code,variant),methods) in enumerate(sorted(groups.items()),1):
            if expected_methods is None: expected_methods=set(methods)
            if set(methods)!=expected_methods:
                raise ValueError('Unequal method coverage; missing controlled comparator')
            query,documents=texts[variant]
            uris=sorted({r['esco_uri'] for rs in methods.values() for r in rs})
            scores={};missing=[]
            for uri in uris:
                doc=documents[uri_index[uri]]
                key=fingerprint([namespace,query[code],doc])
                found=cache.execute('SELECT score FROM scores WHERE key=?',(key,)).fetchone()
                if found is not None:
                    scores[uri]=found[0];reused+=1
                else:missing.append((uri,key,doc))
            for offset in range(0,len(missing),a.batch_size):
                batch=missing[offset:offset+a.batch_size]
                values=score_pairs(model,[(query[code],doc) for _,_,doc in batch],a.batch_size)
                for (uri,key,_),value in zip(batch,values):
                    scores[uri]=value
                    cache.execute('INSERT OR REPLACE INTO scores VALUES (?,?)',(key,value))
                computed+=len(batch)
                cache.commit()
            for method,rs in sorted(methods.items()):
                if len(rs)!=100 or len({r['esco_uri'] for r in rs})!=100:
                    raise ValueError('Expected 100 unique hybrid candidates')
                ranked=sorted(rs,key=lambda r:(-scores[r['esco_uri']],r['esco_uri']))
                for rank,r in enumerate(ranked,1):
                    writer.writerow(dict(run_id=a.run_id,method=method+'_qwen3_reranked',input_variant=variant,
                        masco_version='2020',masco_code=code,esco_version='1.2.1',esco_uri=r['esco_uri'],rank=rank,
                        score=f'{scores[r["esco_uri"]]:.10f}',score_type='yes_minus_no_logit_not_equivalence_probability',
                        hybrid_rank=r['rank'],candidate_origin='fresh_reranking',review_status='unreviewed'))
                    count+=1
            f.flush()
            if n%5==0 or n==1:
                print(n,'/',len(groups),'source/views; computed',computed,'reused',reused,
                    'elapsed',round(time.time()-start,1),flush=True)
    if len(groups)!=len(roles)*len(variants):
        raise ValueError('Incomplete source coverage')
    cache.close()
    temp.rename(out/'candidates.csv')
    save(out/'run.json',dict(config,run_id=a.run_id,status='completed',query_count=len(roles),variants=variants,
        candidate_rows=count,new_pair_computations=computed,reused_pair_scores=reused,
        candidate_sha256=sha(out/'candidates.csv'),elapsed_seconds=round(time.time()-start,2),
        environment_sha256=sha(ROOT/'requirements-v2.lock.txt'),sanity_scores=sanity,human_validation=False,
        measured_accuracy=None,score_interpretation='Relevance logit, not an equivalence probability'))
    print('Completed',a.run_id,count,'candidate rows',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--runs',nargs='+',required=True)
    p.add_argument('--run-id',required=True)
    p.add_argument('--scope',choices=['calibration','review','full'],default='review')
    p.add_argument('--device',default='cpu')
    p.add_argument('--dtype',choices=['float32','bfloat16'],default='float32')
    p.add_argument('--batch-size',type=int,default=16)
    main(p.parse_args())
