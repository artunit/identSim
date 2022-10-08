"""
identSim.py - an implementation of document similarity

This is an implementation of the process described here:

https://dev.to/thepylot/compare-documents-similarity-using-python-nlp-4odp

Usage (see list of options):
    identSim.py [-h] 

For example (where imgs is folder):
    identSim.py -f imgs -d doc/label_odw.txt

- art rhyno, u. of windsor & ourdigitalworld
"""

import argparse, glob, os, sys
import gensim
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize, word_tokenize
import numpy as np

#define TMP direcory
TMP = '/tmp/'
#define INDEX (for reuse)
INDEX = 'sim_index'
#define DICT (for reuse)
DICT = 'sim_dict'
#define TFID
TFID = 'sim_tfid'

#parser arguments
parser = argparse.ArgumentParser()
arg_named = parser.add_argument_group("named arguments")
arg_named.add_argument("-f","--folder", 
    help="input folder, for example: hocrs")
arg_named.add_argument('-d', '--document',
    help="candidate document")
arg_named.add_argument("-n","--num", default=5, type=int,
    help="number of matches to show")

args = parser.parse_args()

if args.folder == None or not os.path.exists(args.folder):
    print("missing input folder, use '-h' parameter for syntax")
    sys.exit()

if args.document == None or not os.path.exists(args.document):
    print("missing input document, use '-h' parameter for syntax")
    sys.exit()

ids = []
doc_coll= []

for num,fn in enumerate(sorted(glob.glob(args.folder + "/*.txt"))):
    with open(fn, 'r') as file:
        if not os.path.exists(DICT) or not os.path.exists(TFID):
            if num == 0:
                print("collect sentence tokens...")
            text = file.read().replace('\n', '')
            doc_coll.append(sent_tokenize(text))
        ids.append(fn)

if not os.path.exists(DICT) or not os.path.exists(TFID):
    print("separate into words...")
    gen_docs = []
    for doc in doc_coll:
        gen_doc = []
        for sent in doc:
            gen_doc += [w.lower() for w in word_tokenize(sent)]
        gen_docs += [gen_doc]

if not os.path.exists(DICT):
    print("build dictionary...")
    dictionary = gensim.corpora.Dictionary(gen_docs)
    dictionary.save(DICT)
else:
    print("load dictionary...")
    dictionary = gensim.corpora.Dictionary.load(DICT)
 
if not os.path.exists(TFID):
    print("now corpus...")
    corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]
    print("create TFID...")
    tf_idf = gensim.models.TfidfModel(corpus)
    tf_idf.save(TFID)
else:
    print("load TFID...")
    tf_idf = gensim.models.TfidfModel.load(TFID)

if not os.path.exists(INDEX):
    print("create similarity index...")
    sims = gensim.similarities.Similarity(TMP,tf_idf[corpus],
        num_features=len(dictionary))
    sims.save(INDEX)
else:
    print("load similarity index...")
    sims = gensim.similarities.Similarity.load(INDEX)

print("prep query_doc...")
with open(args.document, 'r') as file:
     text = file.read().replace('\n', '')
     query_doc = [w.lower() for w in word_tokenize(text)]
    
print("search for similarity...")
query_doc_bow = dictionary.doc2bow(query_doc)
query_doc_tf_idf = tf_idf[query_doc_bow]

print("reverse sort scores...")
-np.sort(-sims[query_doc_tf_idf]) #sort in descending order

print("show results...")
for i in range(args.num):
    ind = np.argsort(-sims[query_doc_tf_idf])[i]
    print("sim match:", ids[ind])
    print("score: ", sims[query_doc_tf_idf][ind])
