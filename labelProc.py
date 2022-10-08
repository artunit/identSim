"""
labelProc.py - step through images with some variations

This simple program applies some image preprocessing
steps and runs Tesseract on the results on all of
them. The target images (78 record labels) have
many different backgrounds, see:

https://archive.org/details/georgeblood

The image modifications are set in OPTS and
use scribo-cli, see:

https://github.com/OCR-D/ocrd_olena

The original image is tried as well.

Usage (see list of options):
    labelProc.py [-h] 

For example:
    labelProc.py -f img_folder

- art rhyno, u. of windsor & ourdigitalworld
"""

import argparse, glob, os, sys
from subprocess import call

#set paths for scribo-cli and tesseract
OCRD_CMD = "/usr/local/bin/scribo-cli"
OPTS = ["sauvola_ms", "wolf", "singh"] #thanks to Merlijn Wajer for these suggestions
TESS_CMD = "/usr/local/bin/tesseract"

""" avoid applying multiple binarization steps """
def isOpt(img,ext):
    for o in OPTS:
        if "_%s.%s" % (o,ext) in img:
            return True
    return False

#parser arguments
parser = argparse.ArgumentParser()
arg_named = parser.add_argument_group("named arguments")
arg_named.add_argument("-e","--ext", 
    default="jpg",
    help="extension")
arg_named.add_argument("-f","--folder", 
    help="input folder")
arg_named.add_argument('-l', '--lang', type=str, 
    default="eng",
    help="language for OCR")

args = parser.parse_args()

if args.folder == None or not os.path.exists(args.folder):
    print("missing folder, use '-h' parameter for syntax")
    sys.exit()

for img in sorted(glob.glob(args.folder + "/*." + args.ext)):
    print("img", img)
    img_base = img.rsplit('.', 1)[0] 

    for opt in OPTS:
        if not isOpt(img,args.ext):
            img_result = "%s_%s.%s" % (img_base,opt,args.ext)
            if not os.path.exists(img_result):
                cmd_line = "%s %s %s %s" % (OCRD_CMD,opt,img,img_result)
                print("cmd_line:", cmd_line)
                call(cmd_line, shell=True)

    for fn in sorted(glob.glob(img_base + "*." + args.ext)):
        fn_base = fn.split(".")[0]
        hocr_fn = fn_base + ".hocr"
        if not os.path.exists(hocr_fn):
            cmd_line = "%s -l %s %s %s hocr" % (TESS_CMD,args.lang,fn,fn_base)
            print("tesseract cmd:", cmd_line)
            call(cmd_line, shell=True)
