"""
mergeHocr.py - merge hocr files together

Usage (see list of options):
    mergeHocr.py [-h] 

For example:
    mergeHocr.py -f imgs

This is a quick modification of a program we
use for major paper scanning. It is not well
tested but the idea is to try to select the
best of several OCR runs.

- art rhyno, u. of windsor & ourdigitalworld
"""

import xml.etree.ElementTree as ET
import argparse, glob, math, os, sys, time
import copy
import glob
from xml.dom import minidom
from subprocess import call

#set paths for cat and lynx
CAT_CMD = "/bin/cat"
LYNX_CMD = "/usr/bin/lynx"

#namespace for HOCR
HOCR_NS = 'http://www.w3.org/1999/xhtml'

""" page_region - a rectangle on the image """
class page_region:
    def __init__(self, x0, y0, x1, y1):
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

""" word_region - word hocr info """
class word_region:
    def __init__(self, wregion, pident, sident, dident, wtext, wline, wconf):
        self.wregion = wregion
        self.pident = pident
        self.sident = sident
        self.dident = dident
        self.wtext = wtext
        self.wline = wline
        self.wconf = wconf

""" par - paragraph hocr """
class par_region:
    def __init__(self, phocr, pregion):
        self.phocr = phocr
        self.pregion = pregion

""" avoid passing through divs with no text """
def isTextinDiv(elem):
    words = ''

    for word_elem in elem.iterfind('.//{%s}%s' % (HOCR_NS,'span')):
        class_name = word_elem.attrib['class']
        if class_name == 'ocrx_word':
            words += word_elem.text

    if len(words.strip()) > 0:
        return True

    return False

""" pull coords and sometimes conf from bbox string """
def getBBoxInfo(bbox_str):
    conf = None

    if ';' in bbox_str:
        bbox_info = bbox_str.split(';')
        bbox_info = bbox_info[1].strip()
        bbox_info = bbox_info.split(' ')
        conf = int(bbox_info[1])
    bbox_info = bbox_str.replace(';',' ')
    bbox_info = bbox_info.split(' ')
    x0 = int(bbox_info[1])
    y0 = int(bbox_info[2])
    x1 = int(bbox_info[3])
    y1 = int(bbox_info[4])

    return x0,y0,x1,y1,conf

""" look for limits of coord boxes """
def calcBoxLimit(low_x, low_y, high_x, high_y, region):
                
    if low_x == 0 or region.wregion.x0 < low_x:
        low_x = region.wregion.x0
    if low_y == 0 or region.wregion.y0 < low_y:
        low_y = region.wregion.y0
    if high_x == 0 or region.wregion.x1 > high_x:
        high_x = region.wregion.x1
    if high_y == 0 or region.wregion.y1 > high_y:
        high_y = region.wregion.y1

    return low_x, low_y, high_x, high_y

""" remove all divs except for ocr_page parent """
def stripPage(orig_page):
    parent_node = None

    for elem in orig_page.iter():
        if elem.tag.startswith("{"):
            elem_tag = elem.tag.split('}', 1)[1]  #strip namespace
        if elem_tag == "div":
            if elem.attrib["class"] == 'ocr_page':
                parent_node = elem
                for child in list(elem): #list is needed for this to work
                    elem.remove(child)

    return parent_node

""" sort by par/sequence order """
def getParInfo(p):
    return p.sident

""" sort by area """
def getArea(r):
    w = abs(r.wregion.x1 - r.wregion.x0)
    h = abs(r.wregion.y1 - r.wregion.y0)

    return (w * h)
        
""" write hocr file """
def writeModHocr(new_node,hocr_file):

    #use minidom pretty print feature
    xmlstr = minidom.parseString(ET.tostring(new_node)).toprettyxml(indent="   ")
    with open(hocr_file, 'w') as f:
        f.write(xmlstr)
    f.close()

""" determine if word is duplicate or should be swapped """
def sortOutWord(word_text,nx0,ny0,nx1,ny1,conf,npar_regions,munge):
    nconf = conf
    ntext = word_text
    nindex = -1

    for ncnt,nregion in enumerate(npar_regions):
        x0 = nregion.wregion.x0
        y0 = nregion.wregion.y0
        x1 = nregion.wregion.x1
        y1 = nregion.wregion.y1

        if abs(nx0 - x0) <= munge and abs(nx1 - x1) <= munge:
            if abs(ny0 - y0) <= munge and abs(ny1 - y1) <= munge:
                if nregion.wconf < conf:
                    return conf,ntext,ncnt
                else:
                    return -1,ntext,-1
       
    return nconf,ntext,nindex
            
""" resize overlapping text (if needed) """
def sortOutCoords(region,par_regions,start):
                
    flag = False
    x0 = region.wregion.x0
    y0 = region.wregion.y0
    x1 = region.wregion.x1
    y1 = region.wregion.y1
                
    for cregion in par_regions[start:]:
        bx0 = cregion.wregion.x0
        by0 = cregion.wregion.y0
        bx1 = cregion.wregion.x1
        by1 = cregion.wregion.y1

        #overlap on x
        if (x0 < bx0 and x1 > bx0) or (x0 > bx0 and x0 < bx1):
            #overlap on y
            if (y0 < by0 and y1 > by0) or (y0 > by0 and y0 < by1):
                flag = True

                #cut box based on length of overlap
                nx0 = x0
                ny0 = y0
                nx1 = x1
                ny1 = y1

                if nx0 > bx0 and nx0 < bx1 and nx1 > bx1:
                    nx0 = bx1
                if nx0 < bx0 and nx1 > bx0: 
                    nx1 = bx0 

                if ny0 > by0 and ny0 < by1 and ny1 > by1:
                    ny0 = by1
                if ny0 < by0 and ny1 > by0:
                    ny1 = by0 
             
                xAdj = (x1 - x0) - (nx1 - nx0)
                yAdj = (y1 - y0) - (ny1 - ny0)

                if xAdj > yAdj and xAdj > 0 and yAdj > 0:
                    region.wregion.y0 = ny0
                    y0 = region.wregion.y0
                    region.wregion.y1 = ny1
                    y1 = region.wregion.y1
                else:
                    region.wregion.x0 = nx0
                    x0 = region.wregion.x0
                    region.wregion.x1 = nx1
                    x1 = region.wregion.x1

    return flag
    
""" get rid of overlaps """
def cleanUpCoords(par_regions):
 
    for cnt,region in enumerate(par_regions):
            if cnt < len(par_regions):
               sortOutCoords(region,par_regions,cnt + 1)

""" add headers for HOCR """
def addHtmlHeaders(img_base):
    html_node = ET.Element(ET.QName(HOCR_NS,"html"))
    head_element = ET.Element(ET.QName(HOCR_NS,"head"))
    title_element = ET.Element(ET.QName(HOCR_NS,"title"))
    head_element.append(title_element)
    html_node.append(head_element)

    return html_node


""" add divs for paragraphs """
def runThruPars(img_base,par_regions,orig_page,conf,lang):
    global file_cnt, page_cnt, block_cnt, par_cnt, line_cnt, word_cnt

    orig_node = stripPage(orig_page)
    parent_node = addHtmlHeaders(img_base)
    body_node = ET.Element(ET.QName(HOCR_NS,"body"))

    l_low_x = 0
    l_low_y = 0
    l_high_x = 0
    l_high_y = 0

    p_low_x = 0
    p_low_y = 0
    p_high_x = 0
    p_high_y = 0

    div_element = ET.Element(ET.QName(HOCR_NS,"div"))
    div_element.set('class','ocr_carea')
    div_element.set('id','block_1_%d' % block_cnt)

    p_element = ET.Element(ET.QName(HOCR_NS,"p"))
    p_element.set('class','ocr_par')
    p_element.set('lang',lang)
    p_element.set('id','par_1_%d' % par_cnt)

    wline = ''
    wpar = ''
    wdiv = ''
    l_element = None

    num_pars = len(par_regions) - 1

    #words in paras
    for cnt, region in enumerate(par_regions):

        w_element = ET.Element(ET.QName(HOCR_NS,"span"))
        w_element.set('class','ocrx_word')

        w_element.text = region.wtext
        w_element.set('title','bbox %d %d %d %d; x_wconf %d' %
            (region.wregion.x0,region.wregion.y0,
            region.wregion.x1,region.wregion.y1,
            region.wconf))
        w_element.set('id','word_1_%d' % word_cnt)
        word_cnt += 1

        if wline != region.wline:
            if l_element is not None:
                l_element.set('title','bbox %d %d %d %d; %s' %
                    (l_low_x,l_low_y,l_high_x,l_high_y,wline))
                l_element.set('id','line_1_%d' % line_cnt)
                line_cnt += 1
                p_element.append(l_element)

            l_element = ET.Element(ET.QName(HOCR_NS,"span"))
            l_element.set('class','ocr_line')
            l_low_x = 0
            l_low_y = 0
            l_high_x = 0
            l_high_y = 0

        l_low_x, l_low_y, l_high_x, l_high_y = calcBoxLimit(
            l_low_x, l_low_y, l_high_x, l_high_y, region)

        if l_element is not None:
            l_element.append(w_element)
            wline = region.wline

            if (wpar != region.pident or cnt == num_pars) and len(wpar) > 0:
                p_element.set('title','bbox %d %d %d %d' %
                    (p_low_x, p_low_y, p_high_x, p_high_y))
                p_element.set('id','par_1_%d' % par_cnt)
                par_cnt += 1
                if cnt == num_pars:
                    if (l_low_x + l_low_y + l_high_x + l_high_y) > 0:
                        l_element.set('title','bbox %d %d %d %d; %s' %
                            (l_low_x,l_low_y,l_high_x,l_high_y,wline))
                        l_element.set('id','line_1_%d' % line_cnt)
                    p_element.append(l_element)
                
                div_element.append(p_element)
                if cnt != num_pars:
                    p_element = ET.Element(ET.QName(HOCR_NS,"p"))
                    p_element.set('class','ocr_par')
                    p_element.set('lang',lang)
                    p_low_x = 0
                    p_low_y = 0
                    p_high_x = 0
                    p_high_y = 0

            p_low_x, p_low_y, p_high_x, p_high_y = calcBoxLimit(
                p_low_x, p_low_y, p_high_x, p_high_y, region)

            if (wdiv != region.dident or cnt == num_pars) and len(wdiv) > 0:
                div_element.set('id','block_1_%d' % block_cnt)
                block_cnt += 1
                orig_node.append(div_element)
                if cnt != num_pars:
                    div_element = ET.Element(ET.QName(HOCR_NS,"div"))
                    div_element.set('class','ocr_carea')

            wpar = region.pident
            wdiv = region.dident

    if len(par_regions) > 0:
        body_node.append(orig_node)
        parent_node.append(body_node)
        writeModHocr(parent_node, img_base + '_odw.hocr')
        if os.path.exists(img_base + '_odw.hocr'):
             cmd_line = "%s %s_odw.hocr | %s -stdin --dump > %s_odw.txt" % (CAT_CMD,img_base,LYNX_CMD,img_base)
             print("cmd: ", cmd_line)
             call(cmd_line, shell=True)

""" include sequence number in word/par ids """
def addSeq(file_cnt,block_id,num):
    seq_id = 'seq_00000_00000'
    if '_' in block_id:
        block_info = block_id.split('_')
        num_id = int(block_info[2])
        #add space for insertions
        seq_id = '%s_%s_%05d_%05d_%05d_%05d' % (block_info[0],
            block_info[1],
            int(block_info[2]) + 1,
            file_cnt,num_id,num)
    return seq_id

""" pull together paragraphs from hocr file """
def sortOutHocr(tree,HOCRfile,HOCRconf,file_cnt,munge,pars):

    #keep words together in paragraphs identified by tesseract
    for div_elem in tree.iterfind('.//{%s}%s' % (HOCR_NS,'div')):
        if 'class' in div_elem.attrib:
            class_name = div_elem.attrib['class']
            if class_name == 'ocr_page': 
                seq_num = 0
                for par_elem in div_elem.iterfind('.//{%s}%s' % (HOCR_NS,'p')):
                    line_info = None
                    if 'class' in par_elem.attrib:
                        class_name = par_elem.attrib['class']
                        if class_name == 'ocr_par': 
                            words = ''
                            for word_elem in par_elem.iterfind('.//{%s}%s' % (HOCR_NS,'span')):
                                class_name = word_elem.attrib['class']
                                if class_name in 'ocr_line,ocr_caption,ocr_header,ocr_textfloat': 
                                    #save line infos
                                    line_info = word_elem.attrib['title']
                                    line_index = line_info.find(';')
                                    line_info = line_info[line_index + 1:]
                                    line_info = ' '.join(line_info.split())
                                if class_name == 'ocrx_word': #word details
                                    word_text = word_elem.text.strip()
                                    if len(word_text) > 0:
                                        x0,y0,x1,y1,conf = getBBoxInfo(
                                            word_elem.attrib['title'])
                                        ind = -1
                                        if conf >= HOCRconf:
                                            conf, word_text, ind = sortOutWord(word_text,x0,y0,x1,y1,
                                                conf,pars,munge)
                                        if ind > -1:
                                            pars[ind].wconf = conf
                                            pars[ind].wtext = word_text
                                            pars[ind].wregion.x0 = x0
                                            pars[ind].wregion.y0 = y0
                                            pars[ind].wregion.x1 = x1
                                            pars[ind].wregion.y1 = y1
                                        elif conf >= HOCRconf:
                                            pars.append(
                                                word_region(page_region(x0,y0,x1,y1),
                                                HOCRfile + '_' + par_elem.attrib['id'],
                                                HOCRfile + '_' + 
                                                    addSeq(file_cnt,par_elem.attrib['id'],
                                                    seq_num),
                                                HOCRfile + '_' + div_elem.attrib['id'],
                                                word_text,line_info,conf))
                                            seq_num += 1
                                    words += word_text
                            #skip para blocks that don't have any text
                            if len(words.strip()) > 0:
                                print(".",end="",flush=True)

    return pars


""" use word coords to remove already recognized sections """
def runThruHocr(ifile,iconf,file_cnt,munge,pars):
    #blanked out before - this is why logic brief here

    print("sort through hocr words for " + ifile + " ...",end="",flush=True)
    try:
        tree = ET.ElementTree(file=ifile)
    except:
        tree = None
    if tree is not None:
        pars = sortOutHocr(tree,ifile,iconf,file_cnt,munge,pars)
    print("!") #hocr processing is done
    #deal with rogues here?

    return pars

""" write results to file """
def writeHocr(block,fhocr):

    hfile = open(fhocr, "w+b")
    hfile.write(bytearray(block))
    hfile.close()

""" avoid merging on anything but base """
def first_pass(img_base,last_hfn):
    if os.path.exists(img_base + ".hocr") and (last_hfn is None or last_hfn not in img_base):
        if not os.path.exists(img_base + "_odw.hocr"):
            return True
    return False 

#parser values
parser = argparse.ArgumentParser()
arg_named = parser.add_argument_group("named arguments")
arg_named.add_argument("-e","--ext",
    default="jpg",
    help="extension for images")
arg_named.add_argument("-f","--folder", 
    help="input folder, for example: imgs")
arg_named.add_argument("-c","--conf", default=50, type=int,
    help="set confidence number threshold for ocr words")
arg_named.add_argument('-l', '--lang', type=str, 
    default="eng",
    help="language for OCR")
arg_named.add_argument("-m","--munge", default=10, type=int,
    help="try to deal with variations in coordinates")

args = parser.parse_args()

if args.folder == None or not os.path.exists(args.folder):
    print("missing image folder, use '-h' parameter for syntax")
    sys.exit()

last_hfn = None
for hfn in sorted(glob.glob(args.folder + "/*." + args.ext)):
    #use filename to pull everything together
    img_base = hfn.rsplit('.', 1)[0]

    #check to see if anything needs merging
    if first_pass(img_base,last_hfn):

        pars = []
        file_cnt = 0
        for fn in sorted(glob.glob(img_base + "*")):
            if ".hocr" in fn and not "_odw.hocr" in fn:
                pars = runThruHocr(fn,args.conf,file_cnt,args.munge,pars)
                file_cnt += 1

        #sort by area for finding overlaps
        pars.sort(key=getArea,reverse=True)

        #now normalize coordinates if needed
        cleanUpCoords(pars) 

        #use sequence order from Tesseract
        pars.sort(key=getParInfo)

        line_cnt = 0
        orig_page = ET.parse(img_base + ".hocr")

        #hocr numbering starts at 1
        page_cnt = 1
        block_cnt = 1
        par_cnt = 1
        line_cnt = 1
        word_cnt = 1

        runThruPars(img_base,pars,orig_page,args.conf,args.lang)

    if last_hfn is None or last_hfn not in img_base:
        last_hfn = img_base
