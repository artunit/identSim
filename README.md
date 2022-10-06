# identSim
This is an experiment looking for duplicate 78 record labels using the approach suggested in
[this blog post](https://brewster.kahle.org/2022/10/02/pythonistas-up-for-quick-hack-to-test-deduping-78rpm-records-using-document-clustering/).
I found it difficult to get workable OCR for many of the labels so I applied a few image
preprocessing steps and then merged the HOCR results. The code explains this in some detail, but as per the 
blog post, the initial images were collected:
```
ia search "collection:georgeblood" --itemlist | head -100 | parallel -j10 'ia download {} --no-directories --format="Item Image"'
```
In this case, the images were collected in a folder called _test100_. The first python script is used
to apply the image preprocessing using [ImageMagick](https://imagemagick.org/) and 
the OCR with [Tesseract OCR](https://github.com/tesseract-ocr/tesseract):
```
python labelProc.py -f test100
```
There are 3 passes carried out for the OCR, and the results are captured in corresponding HOCR files:
```
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_1.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_2.jpg
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_1.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_2.hocr
```
The second python script combines the HOCR results into one document and creates a text verion:
```
python3 ../mergeHocr.py -f test100
```
The combined results are in two files with a "_odw" suffix:
```
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.hocr
test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.txt
```
The idea is that the resulting HOCR file is the best of the 3 passes of the OCR. I found this was the only way to get
a usable level of OCR for similarity processing but there may be better ways of doing this. Finally, the last script
uses the method [described here](https://dev.to/thepylot/compare-documents-similarity-using-python-nlp-4odp):
```
python identSim.py -f test100 -d doc/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-lu_gbia0412575b_itemimage_odw.txt
[nltk_data] Downloading package punkt to /home/ledsys/nltk_data...
[nltk_data]   Package punkt is already up-to-date!
collect sentence tokens...
seperate into words...
build dictionary...
now corpus...
create Term Frequency - Inverse Document Frequency model...
create similarity index...
now prep query_doc...
reverse sort scores...
best match: test100/78_1-a-handful-of-earth-from-my-dear-mothers-grave-2-the-cruiskeen-lawn_frank-luth_gbia0333184b_itemimage_odw.txt
score:  0.6166634
```
Notice that the document for matching is distinct from the folder holding the rest of the OCR files. I suspect
there could be refinements in the text of the OCR to improve the matching, for example, removing 
branding text, e.g. Columbia, but this is meant to be more of a starting point than a definitive example.
