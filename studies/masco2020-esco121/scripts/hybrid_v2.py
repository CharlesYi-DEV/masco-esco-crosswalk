"""Controlled local retrieval. No model output constitutes a human decision."""
import argparse
import csv
import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from common import ROOT, read_csv, save, sha, write_csv

os.environ.setdefault('TOKENIZERS_PARALLELISM', 'false')
os.environ['HF_HOME'] = str(ROOT/'data/interim/hf_v2')
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

SEED = 20261026
INSTRUCTION = ('Given a Malaysian occupation and explicitly qualified unit-group context, '
               'retrieve ESCO occupations relevant to its occupational activities and scope. '
               'Group context is not a statement of individual duties.')
FIELDS = ['run_id','method','input_variant','masco_version','masco_code','esco_version',
          'esco_uri','rank','score','score_type','bm25_rank','tfidf_rank','dense_rank',
          'candidate_origin','review_status']
INPUTS = ['data/processed/masco_occupations.csv', 'data/processed/masco_group_context.csv',
          'data/processed/esco_occupations.csv']

def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()

def top_indices(scores, k=100):
    scores = np.asarray(scores)
    if not np.isfinite(scores).all():
        raise ValueError('Non-finite ranking scores')
    # Stable input order is canonical URI order, including ties at the cutoff.
    return np.argsort(-scores, kind='stable')[:k]

def rrf(rankings, size, k=100, constant=60):
    scores = np.zeros(size, dtype=np.float64)
    for ranking in rankings:
        if len(set(ranking)) != len(ranking):
            raise ValueError('Collapse duplicate URI hits before fusion')
        for rank, index in enumerate(ranking, 1):
            scores[index] += 1/(constant+rank)
    return top_indices(scores, k), scores

def canonical_inputs(roles, esco, contexts, variant):
    queries = []
    for r in roles:
        text = r['title_original'].strip()  # preserve grade and authority qualifiers
        if variant == 'title_context':
            desc = ' '.join(contexts[r['parent_code']]['description'].split())
            text += '. Unit-group context (not an individual description): '+desc
        queries.append(text)
    documents = []
    for e in esco:
        labels = list(dict.fromkeys([e['title_original']]+[x.strip() for x in e['alt_labels'].splitlines() if x.strip()]))
        text = 'Occupation: '+labels[0]
        if len(labels)>1:
            text += '. Alternative labels: '+'; '.join(labels[1:])
        if variant == 'title_context':
            text += '. Description: '+' '.join(e['description'].split())
        documents.append(text)
    return queries, documents

def lexical_scores(queries, documents):
    char = TfidfVectorizer(analyzer='char_wb', ngram_range=(3,5), sublinear_tf=True, dtype=np.float32)
    docs = char.fit_transform(documents)
    tfidf = (char.transform(queries)@docs.T).toarray()
    count = CountVectorizer(lowercase=True, token_pattern=r'(?u)\b\w+\b', dtype=np.float32)
    dt = count.fit_transform(documents).tocsr()
    lengths = np.asarray(dt.sum(axis=1)).ravel()
    df = np.asarray((dt>0).sum(axis=0)).ravel()
    idf = np.log(1+(len(documents)-df+.5)/(df+.5))
    weighted = dt.copy()
    for i in range(len(documents)):
        start, end = weighted.indptr[i:i+2]
        freq = weighted.data[start:end]
        weighted.data[start:end] = idf[weighted.indices[start:end]]*freq*2.5/(freq+1.5*(.25+.75*lengths[i]/lengths.mean()))
    qt = count.transform(queries)
    qt.data[:] = 1  # unique query terms, fixed k1=1.5, b=.75
    bm25 = (qt@weighted.T).toarray()
    return bm25, tfidf

def load_encoder(key, device, locks, dtype_name='float32'):
    import torch
    from sentence_transformers import SentenceTransformer
    dtype = getattr(torch,dtype_name)
    if key == 'minilm':
        path = ROOT/'sources/raw/minilm_1110a243fdf4706b3f48f1d95db1a4f5529b4d41'
        record = dict(model_id='sentence-transformers/all-MiniLM-L6-v2', revision=path.name[7:])
    else:
        record = locks['jina5' if key.startswith('jina5') else key]
        if record['status'] != 'downloaded':
            raise ValueError(f'Model unavailable: {key}')
        path = ROOT/record['path']
    config = {'vision_config':None, 'audio_config':None} if key == 'gemma2' else {}
    model = SentenceTransformer(str(path), device=device, local_files_only=True,
        trust_remote_code=key.startswith('jina5'), config_kwargs=config,
        model_kwargs={'dtype':dtype})
    if key == 'gemma2':
        # ST 6.2 otherwise routes plain text through an absent multimodal chat template.
        # Preserve the published text forward/pooling path, with no chat rendering.
        for modality in list(model[0].modality_config):
            if modality != 'text':
                model[0].modality_config.pop(modality)
    return model, record

def embed(model, key, texts, is_query, batch_size):
    kwargs = dict(batch_size=batch_size, normalize_embeddings=True,
                  convert_to_numpy=True, show_progress_bar=False)
    if key == 'qwen_embedding':
        kwargs['prompt'] = f'Instruct: {INSTRUCTION}\nQuery: ' if is_query else ''
    elif key == 'gemma2':
        # Explicit formatting avoids accidental double application of a default prompt.
        texts = [('task: search result | query: '+t) if is_query else ('title: none | text: '+t) for t in texts]
        kwargs['prompt'] = ''
    elif key.startswith('jina5'):
        kwargs['task'] = 'text-matching' if key.endswith('matching') else 'retrieval'
        kwargs['prompt_name'] = ('query' if is_query else 'document') if kwargs['task']=='retrieval' else 'document'
    else:
        kwargs['prompt'] = ''
    chunks = []
    for i in range(0,len(texts),256):
        chunks.append(model.encode(texts[i:i+256], **kwargs))
        print(key, 'query' if is_query else 'target', min(i+256,len(texts)), '/',len(texts),flush=True)
    vectors = np.concatenate(chunks).astype(np.float32)
    if not np.isfinite(vectors).all():
        raise ValueError('Non-finite embeddings')
    norms = np.linalg.norm(vectors,axis=1)
    if not np.allclose(norms,1,atol=1e-2):
        raise ValueError('Embeddings must be normalized')
    return vectors/norms[:,None]

def encode_cached(model, key, texts, is_query, batch_size, model_record):
    cache_key = fingerprint(['canonical-v2.1',key,model_record,texts,is_query,INSTRUCTION,str(model.dtype),str(model.device)])
    path = ROOT/'data/interim/v2_vectors'/f'{cache_key}.npy'
    path.parent.mkdir(exist_ok=True, parents=True)
    if path.exists():
        return np.load(path)
    result = embed(model,key,texts,is_query,batch_size)
    np.save(path,result)
    return result

def run(args):
    import torch
    torch.manual_seed(SEED)
    torch.set_num_threads(4)
    np.random.seed(SEED)
    if not re.fullmatch(r'[A-Za-z0-9_-]+',args.run_id):
        raise ValueError('Unsafe run ID')
    out = ROOT/'outputs'/args.run_id
    out.mkdir(exist_ok=False)
    start = time.time()
    spec = json.loads((ROOT/'configs/method_experiments_v2.json').read_text())
    hashes = {p:sha(ROOT/p) for p in INPUTS}
    if hashes != spec['frozen_input_hashes']:
        raise ValueError('Frozen inputs changed')
    roles = read_csv(ROOT/INPUTS[0])
    sample = read_csv(ROOT/'review/sample.csv')
    if args.scope != 'full':
        codes = {r['masco_code'] for r in sample if args.scope == 'review' or r['cohort']=='calibration'}
        roles = [r for r in roles if r['code'] in codes]
    esco = sorted(read_csv(ROOT/INPUTS[2]), key=lambda e:e['concept_uri'])
    if len({e['concept_uri'] for e in esco}) != len(esco):
        raise ValueError('Duplicate target URI')
    ctx = {r['code']:r for r in read_csv(ROOT/INPUTS[1])}
    locks = json.loads((ROOT/'sources/models_v2.lock.json').read_text())
    model, record = load_encoder(args.encoder,args.device,locks,args.dtype)
    rows = []
    diagnostics = []
    for variant in args.variants.split(','):
        queries, documents = canonical_inputs(roles,esco,ctx,variant)
        write_csv(out/f'queries_{variant}.csv',[dict(masco_code=r['code'],text=t) for r,t in zip(roles,queries)])
        write_csv(out/f'targets_{variant}.csv',[dict(esco_uri=e['concept_uri'],text=t) for e,t in zip(esco,documents)])
        bm, tf = lexical_scores(queries, documents)
        q = encode_cached(model,args.encoder,queries,True,args.batch_size,record)
        d = encode_cached(model,args.encoder,documents,False,args.batch_size,record)
        dense = q@d.T
        # Record effective model limits. Actual model prompt token overhead is included where possible.
        diagnostics.append(dict(variant=variant,max_seq_length=model.max_seq_length,
            query_max_unprefixed_tokens=max(len(model.tokenizer.encode(t)) for t in queries),
            target_max_unprefixed_tokens=max(len(model.tokenizer.encode(t)) for t in documents),
            query_over_limit=sum(len(model.tokenizer.encode(t))>model.max_seq_length for t in queries),
            target_over_limit=sum(len(model.tokenizer.encode(t))>model.max_seq_length for t in documents)))
        for i,role in enumerate(roles):
            ranks = [top_indices(scores[i],args.k) for scores in [bm,tf,dense]]
            fused, fusion_scores = rrf(ranks,len(esco),args.k)
            maps = [{int(index):rank for rank,index in enumerate(order,1)} for order in ranks]
            for method,indices,scores in [('bm25',ranks[0],bm[i]),('tfidf',ranks[1],tf[i]),
                (f'dense_{args.encoder}',ranks[2],dense[i]),(f'hybrid_{args.encoder}',fused,fusion_scores)]:
                for rank,index in enumerate(indices,1):
                    rows.append(dict(run_id=args.run_id,method=method,input_variant=variant,
                        masco_version='2020',masco_code=role['code'],esco_version='1.2.1',esco_uri=esco[index]['concept_uri'],
                        rank=rank,score=f'{float(scores[index]):.10f}',score_type='ranking_score_not_probability',
                        bm25_rank=maps[0].get(int(index),''),tfidf_rank=maps[1].get(int(index),''),dense_rank=maps[2].get(int(index),''),
                        candidate_origin='fresh_retrieval',review_status='unreviewed'))
    write_csv(out/'candidates.csv',rows,FIELDS)
    metadata = dict(run_id=args.run_id,status='completed',scope=args.scope,encoder=args.encoder,model=record,
        device=args.device,dtype=args.dtype,query_count=len(roles),target_count=len(esco),k=args.k,
        variants=args.variants.split(','),candidate_rows=len(rows),seed=SEED,inputs=hashes,
        rrf_constant=60,lexical_fit_corpus='ESCO only',alias_policy='one canonical document per URI; unique aliases included once; equal text across methods',
        query_policy='raw titles; no grade or authority removal',numeric_hierarchy_filter=False,
        instruction=INSTRUCTION,diagnostics=diagnostics,script_sha256=sha(__file__),
        candidate_sha256=sha(out/'candidates.csv'),environment_sha256=sha(ROOT/'requirements-v2.lock.txt'),
        elapsed_seconds=round(time.time()-start,2),human_validation=False,measured_accuracy=None)
    save(out/'run.json',metadata)
    print(json.dumps({k:metadata[k] for k in ['run_id','query_count','candidate_rows','elapsed_seconds']},indent=2))

if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--encoder',choices=['minilm','qwen_embedding','gemma2','jina5_retrieval','jina5_matching'],required=True)
    p.add_argument('--scope',choices=['calibration','review','full'],default='full')
    p.add_argument('--variants',default='title,title_context')
    p.add_argument('--run-id',required=True)
    p.add_argument('--device',default='cpu')
    p.add_argument('--dtype',choices=['float32','bfloat16'],default='float32')
    p.add_argument('--batch-size',type=int,default=16)
    p.add_argument('--k',type=int,default=100)
    run(p.parse_args())
