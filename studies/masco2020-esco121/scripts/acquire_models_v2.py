"""Download public snapshots, pin commits, and hash local inference files."""
import os
from common import ROOT, save, sha
os.environ['HF_HOME'] = str(ROOT/'data/interim/hf_v2')
from huggingface_hub import HfApi, snapshot_download

MODELS = {
    'minilm': 'sentence-transformers/all-MiniLM-L6-v2',
    'qwen_embedding': 'Qwen/Qwen3-Embedding-0.6B',
    'qwen_reranker': 'Qwen/Qwen3-Reranker-0.6B',
    'gemma2': 'google/embeddinggemma-2',
    'jina5': 'jinaai/jina-embeddings-v5-text-small',
}

def main():
    dest = ROOT/'sources/models_v2.lock.json'
    import json
    records = json.loads(dest.read_text()) if dest.exists() else {}
    for key, model_id in MODELS.items():
        if records.get(key, {}).get('status') == 'downloaded':
            previous = records[key]
            if previous.get('files') and all((ROOT/previous['path']/name).is_file() and sha(ROOT/previous['path']/name)==expected for name,expected in previous['files'].items()):
                continue
        revision = records.get(key, {}).get('revision') or ('1110a243fdf4706b3f48f1d95db1a4f5529b4d41' if key=='minilm' else HfApi().model_info(model_id).sha)
        path = ROOT/f'sources/raw/minilm_{revision}' if key=='minilm' else ROOT/'sources/raw/models_v2'/key/revision
        records[key] = dict(model_id=model_id, revision=revision,
                            path=str(path.relative_to(ROOT)), status='downloading')
        save(dest, records)
        print('Downloading', key, revision, flush=True)
        try:
            snapshot_download(model_id, revision=revision, local_dir=path,
                              allow_patterns=['*.json','*.txt','*.model','*.safetensors','*.py','README.md','LICENSE*'],
                              ignore_patterns=['onnx/*','openvino/*'], max_workers=4)
            records[key]['files'] = {str(p.relative_to(path)):sha(p) for p in sorted(path.rglob('*'))
                                    if p.is_file() and '.cache' not in p.parts}
            records[key]['status'] = 'downloaded'
        except Exception as e:
            records[key].update(status='download_failed', error=str(e))
        save(dest, records)
        print(key, records[key]['status'], flush=True)

if __name__ == '__main__':
    main()
