"""
labelProc.py - step through images with some variations

This simple program applies 3 image preprocessing
steps and runs Tesseract on the results of all of
them. The target images (78 record labels) have
many different backgrounds, see:

https://archive.org/details/georgeblood

The image modifications are:

1) Remove outer album and leave label:

 convert label.jpg -fuzz 50%% -fill white -opaque black -colorspace gray label_1.jpg

2) Simple grayscale:

 convert label.jpg -colorspace label_2.jpg

And, of course, the original image is tried as well :-)

Usage (see list of options):
    labelProc.py [-h] 

For example:
    labelProc.py -f img_folder

- art rhyno, u. of windsor & ourdigitalworld
"""

import argparse, glob, os, sys
from subprocess import call

#set paths for convert (ImageMagick) and tesseract
CONV_CMD = "/usr/bin/convert"
TESS_CMD = "/usr/bin/tesseract"

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
    cmd_base = "convert %s.%s" % (img_base,args.ext)

    img_result = "%s_1.%s" % (img_base,args.ext)
    if not os.path.exists(img_result):
        cmd_line = cmd_base + " -fuzz 50% -fill white -opaque black -colorspace gray "
        cmd_line += img_result
        print("cmd_line:", cmd_line)
        call(cmd_line, shell=True)

    img_result = "%s_2.%s" % (img_base,args.ext)
    if not os.path.exists(img_result):
        cmd_line = cmd_base + " -colorspace gray "
        cmd_line += img_result
        print("cmd_line:", cmd_line)
        call(cmd_line, shell=True)

    for fn in sorted(glob.glob(img_base + "*.*" + args.ext)):
        fn_base = fn.split(".")[0]
        hocr_fn = fn_base + ".hocr"
        if not os.path.exists(hocr_fn):
            cmd_line = "%s -l %s %s %s hocr" % (TESS_CMD,args.lang,fn,fn_base)
            print("tesseract cmd:", cmd_line)
            call(cmd_line, shell=True)
