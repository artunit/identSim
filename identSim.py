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

#parser arguments
parser = argparse.ArgumentParser()
arg_named = parser.add_argument_group("named arguments")
arg_named.add_argument("-f","--folder", 
    help="input folder, for example: hocrs")
arg_named.add_argument('-d', '--document',
    help="candidate document")

args = parser.parse_args()

if args.folder == None or not os.path.exists(args.folder):
    print("missing input folder, use '-h' parameter for syntax")
    sys.exit()

if args.document == None or not os.path.exists(args.document):
    print("missing input document, use '-h' parameter for syntax")
    sys.exit()

ids = []
doc_coll= []

print("collect sentence tokens...")
for num,fn in enumerate(sorted(glob.glob(args.folder + "/*.txt"))):
    with open(fn, 'r') as file:
        text = file.read().replace('\n', '')
        doc_coll.append(sent_tokenize(text))
        ids.append(fn)

print("seperate into words...")
gen_docs = []
for doc in doc_coll:
    #print("doc", doc)
    gen_doc = []
    for sent in doc:
        gen_doc += [w.lower() for w in word_tokenize(sent)]
    gen_docs += [gen_doc]

print("build dictionary...")
dictionary = gensim.corpora.Dictionary(gen_docs)
 
print("now corpus...")
corpus = [dictionary.doc2bow(gen_doc) for gen_doc in gen_docs]

print("create Term Frequency - Inverse Document Frequency model...")
tf_idf = gensim.models.TfidfModel(corpus)

print("create similarity index...")
sims = gensim.similarities.Similarity(TMP,tf_idf[corpus],
    num_features=len(dictionary))

print("now prep query_doc...")
with open(args.document, 'r') as file:
     text = file.read().replace('\n', '')
     query_doc = [w.lower() for w in word_tokenize(text)]

query_doc_bow = dictionary.doc2bow(query_doc)
query_doc_tf_idf = tf_idf[query_doc_bow]

print("reverse sort scores...")
-np.sort(-sims[query_doc_tf_idf]) #sort in descending order
#get index of highest score
ind = np.argsort(-sims[query_doc_tf_idf])[0]

#show results
print("best match:", ids[ind])
print("score: ", sims[query_doc_tf_idf][ind])
