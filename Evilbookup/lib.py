#!/usr/bin/python
# -*- coding: utf-8 -*-
# Authors: Kulverstukas, kenjoe41
# Date: 2015.10.08
# Website: http://Evilzone.org; http://9v.lt/blog
# Description:
#   Automatic ebook (pdf) uploader. Converts first 10 pages of the PDF
#   into text and extracts the ISBN, by which it then extracts more info
#   from worldcat.org or amazon, uploads the file to EZ and generates BBCode.
#   if the file isn't pdf, it tries to convert it to pdf then continues
from __future__ import print_function

import re
import os
import shutil
import sys
import time
import json

from cStringIO import StringIO
from html2bbcode.parser import HTML2BBCode
from robobrowser import RoboBrowser
import mechanize
from goto import with_goto
from subprocess import Popen, PIPE

from evilupload import evilupload
from hide import hide

AMAZON_URL = 'http://www.amazon.com/gp/product/'
ezup = evilupload()
br = RoboBrowser(history=True, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')
mbr = mechanize.Browser()#TODO:turn all instances of mechanize to RoboBrowser

booklog = []
evilbookup_folder = os.path.join(os.path.expanduser('~'), 'evilbookup')  #hide('evilbookup')
bbcodedir = os.path.join(evilbookup_folder, 'bbcode')

#this makes all the directories we need. Including the Evilbookup folder.
if not os.path.isdir(bbcodedir):
    os.makedirs(bbcodedir)

#create log file if not exist
open(os.path.join(evilbookup_folder, 'log.json'), 'a').close()

def login(name=None, passwd=None):
    ''''Logs into https://evilzone.org and returns a working cookies'''
    ezLogin = ezup.login(name,passwd)
    if ezLogin is not None:
        print('Login to Evilzone successful.')
        return ezLogin
    else:
        print('Login to Evilzone failed, try again please.')
        sys.exit()

def convertPdf(path):
    '''Converts PDF to TXT to get the text data'''
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage

#    print('Collecting ISBN from {}'.format(path))
    rsrcmgr = PDFResourceManager()
    retstr = StringIO()
    codec = 'utf-8'
    laparams = LAParams()
    device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
    fp = file(path, 'rb')
    interpreter = PDFPageInterpreter(rsrcmgr, device)
    password = ""
    maxpages = 0
    caching = True
    pagenos=set(range(1, 10))
    for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, \
                password=password,caching=caching, check_extractable=True):
        interpreter.process_page(page)
    fp.close()
    device.close()
    str = retstr.getvalue()
    retstr.close()
    return str

def worldcatInfo(isbn):
    '''Extracts information about an ISBN from worldcat.org.
    Title, summary and bookimg'''

#    print('Collecting book info of ISBN: {} from WorldCat'.format(isbn))
    result = {"title":"", "review":"", "image":""}
    mbr.addheaders = [('User-agent', ' Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')]
    mbr.set_handle_robots(False)
    mbr.open("http://www.worldcat.org/search?qt=worldcat_org_all&q=%s" % isbn)
    try:
        resp = mbr.follow_link(url_regex="title*", nr=0).read() # first link
    except Exception as e:
        print('Error in worldcat: %s'%e)
        return result

    title = re.search("<h1 class=\"title\">.+?</h1>", resp)
    if title:
        result["title"] = title.group(0).replace("<h1 class=\"title\">", "").replace("</h1>", "")
    
    summary = re.search("<div id=\"summary\">.+?</div>", resp, re.DOTALL)
    if not summary:
        summary = re.search("<p class=\".*?review\">.+?</p>", resp, re.DOTALL)
        if summary:
            repl = re.search("<p class=\".*?review\">", summary.group(0))
            result["review"] = summary.group(0).replace(repl.group(0), "").replace("</p>", "").strip()
    else:
        repl = re.search("<div id=\"summary\">", summary.group(0))
        result["review"] = summary.group(0).replace(repl.group(0), "").replace("</div>", "").strip()
    repl = re.search("<span.+?showMoreLessContentElement.+?>", result["review"])
    if repl:
        result["review"] = result["review"].replace(repl.group(0), "").replace("</span>", "")
        repl = re.search("<span.+?showMoreLessControlElement.+", result["review"], re.DOTALL)
        result["review"] = result["review"].replace(repl.group(0), "").strip()
        
    imgUrl = re.search("<img class=\"cover\".+?/>", resp)
    if imgUrl:
        repl = re.search("src=\".+?jpg", imgUrl.group(0))
        result["image"] = "http:"+repl.group(0).replace("src=\"", "")
    
    return result

def isbn13to10(isbn13):
    '''
    Convert an ISBN13 number to ISBN10 by chomping off the
    first 3 digits, then calculating the ISBN10 check digit 
    for the next nine digits to come up with the ISBN10:
    http://en.wikipedia.org/wiki/International_Standard_Book_Number#ISBN-10_check_digit_calculation
    '''
    first9 = isbn13[3:][:9]
    isbn10 = first9 + isbn10_check_digit(first9)
    return isbn10

def isbn10_check_digit(isbn10):
    '''
    Given the first 9 digits of an ISBN10 number calculate
    the final (10th) check digit: 
    http://en.wikipedia.org/wiki/International_Standard_Book_Number#ISBN-10_check_digit_calculation
    '''
    i = 0
    s = 0

    for n in xrange(10,1,-1):
        s += n * int(isbn10[i])
        i += 1

    s = s % 11
    s = 11 - s
    v = s % 11
        
    if v == 10:
        return 'x'
    else:
        return str(v)

def is13(isbn):
    '''Checks if an ISBN is ISBN13'''
    if isbn.startswith('978') or isbn.startswith('979'):
        return True
    return False
     
def clean_isbn(isbn):
    isbn = ''.join(re.findall(r'\d+', isbn))
    if is13(isbn):
        isbn = isbn13to10(isbn)
    return isbn

def amazonInfo(isbn):
    '''
    Get the Amazon review for each book in books[]
    '''

#    print('Collecting Book info for ISBN: {} from amazon'.format(isbn))
    image = review = ''
    results  = {"title":"", "review":review, "image":image}
    url = AMAZON_URL + str(isbn)
    br.open(url)
    html = br.response.content
    
    try:
        tpat = re.compile(r'<span id="productTitle" class="a-size-large">(.*?)</span>')
        results['title'] = tpat.findall(html)[0]
    
        ipat = re.compile(r'data-a-dynamic-image="{&quot;(.*?)&quot;')
        results['image'] = ipat.findall(html)[0]

        rpat = re.compile('<noscript>(.*?)</noscript>', re.DOTALL)
        review = rpat.findall(html)[1]
        results['review'] = html2bbcode(review)

        return results
    except IndexError as e:
        #no results for this ISBN
        #print('IndexError in amazon')
        return results    

def html2bbcode(html):
    parser = HTML2BBCode()
    bbcode = str(parser.feed(str(html)))
    return bbcode


def sanitizeFilename(filename):
    '''Cleans up a filename to remove unallowed characters'''
    #This function is momentarily disabled till original author says otherwise.
    allowedSymbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321.-_ ()[]+,~"
    newFilename = filename.split(".")[0]
    for symbol in filename:
        if (symbol not in allowedSymbols):
            newFilename = newFilename.replace(symbol, "")
    if (len(newFilename) > 47):
        newFilename = newFilename[:46].strip()
    newFilename = newFilename.replace(" ", "_")+".pdf"
    return newFilename

def getBooksIndex():
    #secInAweek = 604800
    indexfile = os.path.join(evilbookup_folder, 'books_index.json')

    #this nonsense here is to not grab the index everytime, thewormkill doesn't update it that much.
    #feel free to coment out this try block if you need it updated everytime.
    #i wouldn't uncomment it till it works well.
    #try:
    #    with open(indexfile, 'r') as f:
    #        last_update = ast.literal_eval(f.readline().strip())
    #        next_update = last_update[1] + secInAWeek
    #        seconds_now = time.mktime(time.localtime())
    #        if  next_update < int(seconds_now):
    #            return
    #except:
    #    pass

    url='https://evilzone.org/wiki//index.php/The_big_ebook_index'
    br.open(url)
    html=br.response.content

    if os.path.exists(indexfile):
        os.remove(indexfile)

    #with open(os.path.join(evilbookup_folder, 'books_index.json'), 'w+') as f:
    #    f.write('last update of Book Index, {}\n'.format(str(time.mktime(time.localtime()))))

    index = []
    for link in br.find_all("a"):
        url = link.get("href")
        
        #dirty url elimination, damn you thewormkill
        #an lxml pattern could have been easy
        if url: 

            if url.startswith('#') or \
               url.startswith('/wiki') or \
               '//www.mediawiki.org/' in url or \
               url == 'https://evilzone.org/wiki//index.php?title=The_big_ebook_index&oldid=':
                continue
            index.append({'title':link.text, 'url':url})
    with open(os.path.join(evilbookup_folder, 'books_index.json'), 'a+') as f:
        json.dump(index, f)
    print('Updated your local copy of the Evilzone Book Index.')

def convert2pdf(filename):
    #http://manual.calibre-ebook.com/cli/ebook-convert.html

    print('Converting {} to PDF'.format(path))
    filenm, ext = os.path.splitext(filename)
    pdfname = filenm+'.pdf'
    try:
        process = Popen(['ebook-convert', filename, pdfname], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        return pdfname
    except OSError:
        print('Error: Calibre\'s ebook-converter not installed.' \
                ' Please install Calibre and continue.',file=sys.stderr)
        sys.exit()

def generateBBCode(upUrl, info, filename):
    if (info["review"] is ""): info["review"] = "No review available :/"
    return "%s\n\n[img]%s[/img]\n\n[quote]%s[/quote]\n\nDownload: [url=%s]%s[/url]"\
                    % (info["title"], info["image"], info["review"], upUrl, filename)

def writeBBcode(goodFilename, upUrl, info):
    #TODO: create folder to hold BBcode and delete as you post on Forum
    #create file to hold the BBcode and file details
    if (os.path.exists(bbcodedir+goodFilename[:-4]+".txt")):
        for num in range(1000):
            if (not os.path.exists(os.path.join(bbcodedir, goodFilename[:-4]+str(num))+".txt")):
                goodFilename = goodFilename[:-4]+str(num)+".txt"
                break
    try:
        with open(os.path.join(bbcodedir, goodFilename[:-4])+".txt", "w") as bbOut: 
            bbOut.write(generateBBCode(upUrl, info,goodFilename))
    except TypeError:
        with open(os.path.join(bbcodedir, goodFilename[:-4])+".txt", "w") as bbOut: 
            bbOut.write(unicode(generateBBCode(upUrl, info, goodFilename), "utf-8"))

def log(title, post_url):
    ''''Log uploaded books to file.'''
    booklog.append({'title':title, 'url':post_url})

def isdupe(title):
    '''Check for duplicate files in index and/or logs of books already posted by you'''
    def dupe_search(title, path):

        #load book index into json of (title, url)
        books = []
        with open(path, 'r') as f:
            try:
                books = json.load(f)
            except ValueError as e:
                pass


        for book in books:
            if book['title'].lower().find(title.lower()) != -1:
                return book
        return False
    return dupe_search(title, (os.path.join(evilbookup_folder, 'books_index.json'))) or\
           dupe_search(title, (os.path.join(evilbookup_folder, 'log.json')))
#TODO
def post():
    #look through bbcode dir
    #for file, grab title, and bbcode, post to EZ
    #remove file
    post_url = None
    return post_url

@with_goto
def process_file(filename):
    #Converting PDF to Text to extract ISBN number.
    print ("Processing '%s'..." % filename)
    text = convertPdf(filename)
    isbns = re.findall('(?:[0-9]{3}-)?[0-9]{1,5}-[0-9]{1,7}-[0-9]{1,6}-[0-9]', text)

    if (len(isbns) > 0):
        isbn = clean_isbn(isbns[0])
        #sanitizeFilename() is disabled till i have a talk with kulverstukas
        goodFilename = filename #sanitizeFilename(filename)
        #os.rename(filename, goodFilename)
        print ("Found ISBN: %s, extracting info..." % isbn)

        print('Getting book details from Amazon...')
        info = amazonInfo(isbn)
                
        if info['review'] is '':
            print('Getting Book Details from Worldcat....')
            info = worldcatInfo(isbn)

        #have failed to get any info on this book, jump to No_ISBN
        #this is metaprogramming not native to python
        try:
            if info['review'] is '':
                goto .isbn_no_info
        except KeyError:
            goto .isbn_no_info
        
        dupe = isdupe(info['title'])
        if dupe: 
            print('\'{0}\' already exists as \'{1}\' @ \'{2}\'. Skipping...'.format(filename, dupe['title'], dupe['url']))
            return			

        #Uploading the file to http://upload.evilzone.org
        print ("Uploading as '%s'...\n" % goodFilename)
        upload_url = ezup.fileupload(goodFilename)
               
        #write BBcode
        writeBBcode(goodFilename, upload_url, info)

        #post this book to Evilzone
        post_url = post()

        #log that all went well with this one. EZ gots it.
        log(info['title']or filename, post_url or upload_url)
    else:
        label .isbn_no_info
        #This is for the books without ISBN detected.
        print ("Didn't find ISBN or any info on file: '%s'\n" % goodFilename)
