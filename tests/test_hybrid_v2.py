import csv
import sys
import tempfile
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'studies/masco2020-esco121/scripts'))
from hybrid_v2 import rrf,top_indices,canonical_inputs,lexical_scores
from expand_review_v2 import collect_pool,blind_rows,BLIND_FIELDS

class Retrieval(unittest.TestCase):
    def test_fusion_rewards_cross_channel_agreement(self):
        order,scores=rrf([[0,1],[2,1],[1,3]],4,4)
        self.assertEqual(order[0],1)
        self.assertAlmostEqual(scores[1],2/62+1/61)
    def test_alias_cannot_vote_twice(self):
        with self.assertRaises(ValueError):rrf([[0,0]],2)
    def test_cutoff_ties_are_deterministic(self):
        self.assertEqual(top_indices([1,1,1],2).tolist(),[0,1])
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError):top_indices([np.nan,1])
    def test_raw_grade_and_qualified_context(self):
        qs,ds=canonical_inputs([dict(title_original='Officer Grade 41',parent_code='0111')],
            [dict(title_original='officer',alt_labels='officer\nagent\nagent',description='scope')],
            {'0111':{'description':'group activities'}},'title_context')
        self.assertIn('Grade 41',qs[0]);self.assertIn('not an individual description',qs[0])
        self.assertEqual(ds[0].count('agent'),1)
    def test_query_does_not_change_idf(self):
        docs=['nurse nursing care','brick mason walls']
        b1,t1=lexical_scores(['nurse'],docs)
        b2,t2=lexical_scores(['nurse','unseen zzzzzz'],docs)
        np.testing.assert_array_equal(b1[0],b2[0]);np.testing.assert_array_equal(t1[0],t2[0])
        self.assertGreater(b1[0,0],b1[0,1])

class Pooling(unittest.TestCase):
    def fixture(self,rows):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        p=Path(d.name)/'c.csv'
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['run_id','method','input_variant','masco_code','esco_uri','rank'])
            w.writeheader();w.writerows(rows)
        return p
    def row(self,method,uri='target'):
        return dict(run_id='synthetic',method=method,input_variant='title',masco_code='0111-01',esco_uri=uri,rank=1)
    def test_missing_method_rejected(self):
        p=self.fixture([self.row('a')])
        with self.assertRaises(ValueError):collect_pool([p],{'0111-01'},{('a','title'),('b','title')},1)
    def test_union_and_dedup(self):
        p=self.fixture([self.row('a'),self.row('b'),self.row('c','extra')])
        pool,_=collect_pool([p],{'0111-01'},{(x,'title') for x in 'abc'},1)
        self.assertEqual(pool['0111-01'],{'target','extra'})
    def test_missing_source_rejected(self):
        p=self.fixture([self.row('a')])
        with self.assertRaises(ValueError):collect_pool([p],{'0111-01','0111-02'},{('a','title')},1)
    def test_blind_output_has_no_method_rank_or_score(self):
        e={'u':dict(code='0',title_original='title',description='description')}
        rows=blind_rows({'0111-01':{'u'}},e,'test',1)
        self.assertEqual(set(rows[0]),set(BLIND_FIELDS))
        self.assertEqual(rows[0]['masco_code'],'0111-01')
        self.assertFalse({'method','rank','score','run_id'} & set(rows[0]))

if __name__=='__main__':unittest.main()
