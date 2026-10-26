"""Exact, unquantized Qwen3 weights on MLX; right padding plus causal attention.

Only hidden states at each real sequence's last token are scored, so future padding
cannot affect them. Project onto the two required output rows instead of all tokens.
"""
import numpy as np
from hybrid_v2 import INSTRUCTION

class MLXQwenScorer:
    def __init__(self,path,device='mps',dtype='bfloat16'):
        import mlx.core as mx
        from mlx_lm import load
        from transformers import AutoTokenizer
        self.mx=mx
        self.model,_=load(str(path))
        self.model.set_dtype(getattr(mx,dtype))
        mx.eval(self.model.parameters())
        self.tokenizer=AutoTokenizer.from_pretrained(str(path),local_files_only=True,padding_side='right')
        self.prefix=self.tokenizer.encode('<|im_start|>system\nJudge whether the Document meets the requirements based on the Query and the Instruct provided. Note that the answer can only be "yes" or "no".<|im_end|>\n<|im_start|>user\n',add_special_tokens=False)
        self.suffix=self.tokenizer.encode('<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n',add_special_tokens=False)
        ids=[self.tokenizer.convert_tokens_to_ids(t) for t in ['no','yes']]
        weights=self.model.model.embed_tokens.weight if self.model.args.tie_word_embeddings else self.model.lm_head.weight
        self.head=weights[mx.array(ids)]
        mx.eval(self.head)

    def predict(self,pairs,batch_size=32,show_progress_bar=False):
        mx=self.mx
        texts=[f'<Instruct>: {INSTRUCTION}\n<Query>: {q}\n<Document>: {d}' for q,d in pairs]
        tokens=self.tokenizer(texts,padding=False,add_special_tokens=False)['input_ids']
        tokens=[self.prefix+t+self.suffix for t in tokens]
        lengths=[len(t) for t in tokens]
        if max(lengths)>2048:
            raise ValueError('Refusing silent reranker truncation')
        padded=[t+[self.tokenizer.pad_token_id]*(max(lengths)-len(t)) for t in tokens]
        hidden=self.model.model(mx.array(padded))
        last=hidden[mx.arange(len(tokens)),mx.array(lengths)-1]
        logits=(last@self.head.T).astype(mx.float32)
        scores=logits[:,1]-logits[:,0]
        mx.eval(scores)
        return np.array(scores)
