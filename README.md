# identSim
This is an experiment to identify duplicate 78 record labels from the always impressive
[Internet Archive](https://archive.org/) using the approach suggested in
[this blog post](https://brewster.kahle.org/2022/10/02/pythonistas-up-for-quick-hack-to-test-deduping-78rpm-records-using-document-clustering/).
I found it difficult to get workable OCR for many of the labels so I applied a few image
preprocessing steps and then merged the HOCR results. The code explains this in some detail, but as per the 
blog post, the initial images were collected:
```
ia search "collection:georgeblood" --itemlist | head -100 | parallel -j4 'ia download {} --no-directories --format="Item Image"'
```
In this case, the images were collected in a folder called _test100_. The first python script is used
to apply the image preprocessing using the [OCRD Olena utility](https://github.com/OCR-D/ocrd_olena) and 
the OCR with [Tesseract OCR](https://github.com/tesseract-ocr/tesseract):
```
python labelProc.py -f test100
```
There are 4 passes carried out for the OCR by default, and the results are captured in corresponding HOCR files:
```
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_sauvola_ms.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_singh.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_wolf.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_sauvola_ms.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_singh.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_wolf.hocr
```
You can skip the OCR step and do this separately (using parallel for example: 
_find test100 -name '*.jpg' | parallel -j4 tesseract {} {.} hocr_) by using the _s_ switch:
```
python labelProc.py -f test100 -s
```
The script is for convenience, all of the above can be done with parallel. The HOCR option in Tesseract 
is used in order to get the probability numbers for OCR accuracy.
The second python script combines the HOCR results into one document based on the probability numbers and creates 
a single combined text verion:
```
python mergeHocr.py -f test100
```
The combined results are in two files with a "_odw" suffix:
```
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.txt
```
The idea is that the resulting HOCR file is the best of the, in this case, 4 passes of the OCR. I found this was one way to get
a usable level of OCR for similarity processing with my test set but there may be better ways of doing this. Finally, the last script
uses the method [described here](https://dev.to/thepylot/compare-documents-similarity-using-python-nlp-4odp):
```
python identSim.py -f test100 -d doc/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.txt
[nltk_data] Downloading package punkt to /home/ledsys/nltk_data...
[nltk_data]   Package punkt is already up-to-date!
collect sentence tokens...
separate into words...
build dictionary...
now corpus...
create TFID...
create similarity index...
prep query_doc...
search for similarity...
reverse sort scores...
show results...
sim match: test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-luth_gbia0333184b_itemimage_odw.txt
score:  1.0000001
sim match: test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.txt
score:  0.43742537
sim match: test100/78_1-a-bushel-and-a-peck-2-my-time-of-day_vivian-blaine-and-the-hot-box-girls-rob_gbia0035785d_itemimage_odw.txt
score:  0.1598242
sim match: test100/78_1-a-basketful-of-nuts_gbia8000354d_itemimage_odw.txt
score:  0.12936018
sim match: test100/78_1-a-wise-bird_laura-littlefield-loomis-johnstone-hollis-dann_gbia0201218a_itemimage_odw.txt
score:  0.11242671
```
Notice that the document for matching is distinct from the folder holding the OCR files. In this case,
the document literally has a copy in the folder, hence the perfect (1.000) match. By default, the
top 5 document matches are shown. The index and associated parts are built on the first invocation,
but are saved and loaded from disk if run multiple times. I suspect
there could be refinements in the text of the OCR to improve the matching, for example, removing 
branding text, e.g. _Columbia_, but this is meant to be more of a starting point than a definitive example.
