"""Search the entire frozen ESCO corpus, independently of any candidate shortlist."""
from common import *
import argparse,re
p=argparse.ArgumentParser();p.add_argument('query');p.add_argument('--limit',type=int,default=30);p.add_argument('--all-terms',action='store_true');a=p.parse_args();terms=a.query.casefold().split();hits=[]
for r in read_csv(ROOT/'data/processed/esco_occupations.csv'):
 text=' '.join([r['concept_uri'],r['code'],r['title_original'],r['alt_labels'],r['description']]).casefold()
 found=[t in text for t in terms]
 if (all(found) if a.all_terms else any(found)):hits.append(r)
print(f'{len(hits)} hits across full frozen corpus. Showing at most {a.limit}; file order, not model rank.')
for r in hits[:a.limit]:print(r['code'],r['title_original'],'\n',r['concept_uri'],'\n',r['description'],'\n')
