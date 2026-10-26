"""Versioned, equal-depth pooling with mandatory method/source coverage."""
import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import defaultdict
from common import ROOT, read_csv, write_csv, save, sha

BLIND_FIELDS=['pair_id','masco_code','display_order','esco_uri','esco_code','esco_title','esco_description']

def collect_pool(paths, sample_codes, expected, depth=10):
    pool=defaultdict(set)
    contributions=[]
    coverage=defaultdict(set)
    top_counts=defaultdict(set)
    for path in paths:
        with path.open(newline='') as f:
            for r in csv.DictReader(f):
                if r['masco_code'] not in sample_codes:
                    continue
                method=(r['method'],r['input_variant'])
                if method not in expected:
                    raise ValueError(f'Unexpected method: {method}')
                if 1<=int(r['rank'])<=depth:
                    code=r['masco_code'];uri=r['esco_uri']
                    pool[code].add(uri)
                    coverage[method].add(code)
                    top_counts[(method,code)].add((int(r['rank']),uri))
                    contributions.append(dict(masco_code=code,esco_uri=uri,run_id=r['run_id'],
                        method=r['method'],input_variant=r['input_variant'],rank=r['rank']))
    if set(coverage)!=set(expected):
        raise ValueError('A required method is missing from the pool')
    for method in expected:
        if coverage[method]!=sample_codes:
            raise ValueError(f'Incomplete source coverage: {method}')
        for code in sample_codes:
            pairs=top_counts[(method,code)]
            if {rank for rank,_ in pairs}!=set(range(1,depth+1)) or len({uri for _,uri in pairs})!=depth:
                raise ValueError(f'Invalid/unequal pooling depth: {method}, {code}')
    return pool, contributions

def blind_rows(pool, esco, version, seed):
    rng=random.Random(seed)
    rows=[]
    for code,uris in sorted(pool.items()):
        order=sorted(uris);rng.shuffle(order)
        for i,uri in enumerate(order,1):
            e=esco[uri]
            pair_id=hashlib.sha256(f'{version}|{code}|{uri}'.encode()).hexdigest()[:20]
            rows.append(dict(pair_id=pair_id,masco_code=code,display_order=i,esco_uri=uri,
                esco_code=e['code'],esco_title=e['title_original'],esco_description=e['description']))
    return rows

def main(a):
    config=json.loads((ROOT/a.config).read_text())
    version=config['review_version']
    out=ROOT/'review'/version
    if out.exists():
        raise FileExistsError('Never overwrite reviewer work; choose a new review version')
    sample=read_csv(ROOT/'review/sample.csv');codes={r['masco_code'] for r in sample}
    expected={tuple(x) for x in config['expected_methods']}
    paths=[ROOT/'outputs'/run/'candidates.csv' for run in config['runs']]
    hashes={}
    for path in paths:
        metadata=json.loads((path.parent/'run.json').read_text())
        if metadata['candidate_sha256']!=sha(path):
            raise ValueError(f'Run hash differs: {path}')
        hashes[str(path.relative_to(ROOT))]=sha(path)
    pool,contributions=collect_pool(paths,codes,expected,config['pool_depth'])
    # Protect the original pool as a subset, not just its generating method names.
    old={(r['masco_code'],r['esco_uri']) for r in read_csv(ROOT/'review/blinded_candidate_pool.csv')}
    pairs={(code,uri) for code,uris in pool.items() for uri in uris}
    if not old.issubset(pairs):
        raise ValueError('Expanded pool must retain every original blinded pair')
    esco={e['concept_uri']:e for e in read_csv(ROOT/'data/processed/esco_occupations.csv')}
    rows=blind_rows(pool,esco,version,config['seed'])
    out.mkdir()
    write_csv(out/'blinded_candidate_pool.csv',rows,BLIND_FIELDS)
    for file in ['sample.csv','unit_partition.csv','reference_pairs.csv','occupation_status.csv']:
        shutil.copy2(ROOT/'review'/file,out/file)
    for i,reviewer in enumerate(['R1','R2'],1):
        write_csv(out/f'{reviewer}_candidate_pool.csv',blind_rows(pool,esco,version,config['seed']+i),BLIND_FIELDS)
        for suffix in ['occupation_worksheet.csv','pair_decisions.csv']:
            src=ROOT/'review'/f'{reviewer}_{suffix}'
            original=read_csv(src)
            # Do not carry annotated decisions into a fresh independent round.
            if suffix=='pair_decisions.csv' and original:
                raise ValueError('Existing annotations need a separately designed carry-forward protocol')
            if suffix=='occupation_worksheet.csv' and any(r.get('occupation_status') or r.get('notes') for r in original):
                raise ValueError('Do not copy filled reviewer worksheets')
            shutil.copy2(src,out/src.name)
    admin=ROOT/'outputs'/f'{version}_pool_audit'
    admin.mkdir(exist_ok=False)
    write_csv(admin/'contributions_not_for_reviewers.csv',contributions)
    write_csv(admin/'pool_sizes.csv',[dict(masco_code=code,pairs=len(uris)) for code,uris in sorted(pool.items())])
    save(admin/'manifest.json',dict(config,candidate_hashes=hashes,
        original_pool_sha256=sha(ROOT/'review/blinded_candidate_pool.csv'),
        sample_sha256=sha(ROOT/'review/sample.csv'),partition_sha256=sha(ROOT/'review/unit_partition.csv'),
        sample_size=len(codes),original_pairs=len(old),expanded_pairs=len(pairs),new_pairs=len(pairs-old),
        methods=len(expected),blinded_pool_sha256=sha(out/'blinded_candidate_pool.csv'),
        source_code_sha256=sha(__file__),human_decisions_added=0,accepted_mappings_added=0))
    (out/'REVIEWER_README.txt').write_text(
        'Independent occupation-scope review, version '+version+'.\n'
        'Use your assigned R1 or R2 pool and worksheets. Do not open outputs or method-provenance files.\n'
        'Display order is randomized; it conveys no model ranking. Candidate presence is not evidence of correctness.\n'
        'Consult the annotation guide and original publication evidence. Group descriptions are not individual duties.\n'
        'Search the complete frozen ESCO corpus beyond this shortlist and record additional targets.\n'
        'An incomplete pool cannot establish that no suitable target exists.\n')
    print(json.dumps(dict(review_version=version,sample_size=len(codes),original_pairs=len(old),
        expanded_pairs=len(pairs),new_pairs=len(pairs-old),methods=len(expected)),indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',default='configs/review_pool_v2.json')
    main(p.parse_args())
