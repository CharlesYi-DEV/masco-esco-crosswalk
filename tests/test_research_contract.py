import sys,unittest,tempfile,subprocess,csv,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'studies/masco2020-esco121/scripts'))
from accept_mappings import build
from common import ROOT

def decision(i,reviewer,stage='independent',uri='target1',relation='equivalent_scope'):
 return dict(decision_id=i,masco_version='2020',masco_code='0111-01',esco_version='1.2.1',esco_uri=uri,relation=relation,review_stage=stage,decision_method='synthetic_test',guide_version='synthetic',reviewer_id=reviewer,reviewer_type='human',reviewed_at='synthetic-test-only',independence_attested='true',source_evidence='synthetic fixture',target_evidence='synthetic fixture',rationale='synthetic fixture',review_status='completed')
class Gate(unittest.TestCase):
 def test_zero_mapping_allowed(self):self.assertEqual(build([],{'0111-01'},{'target1'}),[])
 def test_ai_cannot_adjudicate(self):
  x=decision('d','ai','adjudication');x['reviewer_type']='ai'
  with self.assertRaises(AssertionError):build([x],{'0111-01'},{'target1'})
 def test_single_reviewer_cannot_validate(self):
  with self.assertRaises(AssertionError):build([decision('a','r1'),decision('b','r1'),decision('c','r3','adjudication')],{'0111-01'},{'target1'})
 def test_related_pair_not_accepted(self):
  self.assertEqual(build([decision('a','r1'),decision('b','r2'),decision('c','r3','adjudication',relation='related_insufficient')],{'0111-01'},{'target1'}),[])
 def test_multiple_targets_allowed(self):
  ds=[]
  for uri in ['target1','target2']:
   ds += [decision(uri+'a','r1',uri=uri),decision(uri+'b','r2',uri=uri),decision(uri+'c','r3','adjudication',uri=uri,relation='masco_narrower_than_esco')]
  self.assertEqual(len(build(ds,{'0111-01'},{'target1','target2'})),2)
 def test_missing_evidence_rejected(self):
  d=decision('a','r1');d['source_evidence']=''
  with self.assertRaises(AssertionError):build([d],{'0111-01'},{'target1'})
 def test_unknown_target_rejected(self):
  with self.assertRaises(AssertionError):build([decision('a','r1')],{'0111-01'},{'target2'})
 def test_empty_reference_cannot_produce_metrics(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'metrics.json'
   empty=Path(d)/'empty.csv';empty.write_text('masco_code,esco_uri\n')
   r=subprocess.run([sys.executable,str(ROOT/'scripts/evaluate.py'),'--candidates',str(ROOT/'outputs/smoke_20261026_k10/candidates.csv'),'--reference',str(empty),'--out',str(out)],capture_output=True,text=True)
   self.assertNotEqual(r.returncode,0);self.assertFalse(out.exists());self.assertIn('No reference pairs',r.stderr)
 def test_no_change_version_diff(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'diff.csv';src=Path(d)/'source.csv'
   src.write_text('code,title_original,parent_code\n0111-01,Synthetic occupation,0111\n')
   subprocess.run([sys.executable,str(ROOT/'scripts/compare_versions.py'),str(src),str(src),'--out',str(out)],check=True,capture_output=True)
   with out.open() as f:self.assertEqual(list(csv.DictReader(f)),[])
class Evaluation(unittest.TestCase):
 def run_fixture(self,completeness,independent='true'):
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);candidate=d/'c.csv';ref=d/'r.csv';out=d/'metrics.json'
   with candidate.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['method','input_variant','masco_code','esco_uri','rank']);w.writeheader()
    for i in range(1,11):w.writerow(dict(method='synthetic',input_variant='title',masco_code='0111-01',esco_uri='target'+str(i),rank=i))
   with ref.open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['masco_code','esco_uri','acceptable','reference_completeness','independent_human_reference','adjudication_id']);w.writeheader();w.writerow(dict(masco_code='0111-01',esco_uri='target1',acceptable='true',reference_completeness=completeness,independent_human_reference=independent,adjudication_id='synthetic'))
   result=subprocess.run([sys.executable,str(ROOT/'scripts/evaluate.py'),'--candidates',str(candidate),'--reference',str(ref),'--out',str(out)],capture_output=True,text=True)
   return result,json.loads(out.read_text()) if out.exists() else None
 def test_partial_pool_is_not_recall(self):
  r,data=self.run_fixture('partial_pool');self.assertEqual(r.returncode,0)
  self.assertTrue(all(m['macro_recall_at_k'] is None for m in data['metrics']))
  self.assertEqual(data['metrics'][0]['partial_pool_judged_positive_hit_rate'],1)
 def test_exhaustive_reference_allows_recall(self):
  r,data=self.run_fixture('exhaustive');self.assertEqual(r.returncode,0);self.assertEqual(data['metrics'][0]['macro_recall_at_k'],1)
 def test_ai_reference_is_rejected(self):
  r,data=self.run_fixture('exhaustive','false');self.assertNotEqual(r.returncode,0);self.assertIsNone(data)

if __name__=='__main__':unittest.main()
