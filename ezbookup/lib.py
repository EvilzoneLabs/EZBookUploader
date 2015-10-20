#!/usr/bin/python
# -*- coding: utf-8 -*-
# Authors: Kulverstukas, kenjoe41
# Date: 2015.10.08
# Website: http://Evilzone.org; http://9v.lt/blog
# Description:
#   Automatic ebook (pdf) uploader. Converts first 10 pages of the PDF
#   into text and extracts the ISBN, by which it then extracts more info
#   from worldcat.org, uploads the file to EZ and generates BBCode.
from __future__ import print_function

import re
import os
import shutil
import sys
import evilupload
from evilupload import evilupload
from cStringIO import StringIO
from html2bbcode.parser import HTML2BBCode
from robobrowser import RoboBrowser
import threading
from goto import with_goto
from subprocess import Popen, PIPE

AMAZON_URL = 'http://www.amazon.com/gp/product/'
ezup = evilupload()
br = RoboBrowser(history=True, user_agent='Mozilla/5.0 (Windows NT 6.1; rv:30.0) Gecko/20100101 Firefox/30.0')

def login(name=None, passwd=None):
    ''''Logs into https://evilzone.org and returns a working cookies'''
    ezLogin = ezup.login(name,passwd)
    if ezLogin is not None:
        print('Logged in')
        return ezLogin
    else:
        print('Login failed. Exiting...!')
        sys.exit()

def convertPdf(path):
    '''Converts PDF to TXT to get the text data'''
    from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
    from pdfminer.converter import TextConverter
    from pdfminer.layout import LAParams
    from pdfminer.pdfpage import PDFPage

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
    result = {"title":"", "summary":"", "bookimg":""}

    br.open("http://www.worldcat.org/search?qt=worldcat_org_all&q=%s" % isbn)
    try:
        resp = br.follow_link(url_regex="title*", nr=0).read() # first link
    except:
        return result
    # with open("debug.txt", "w") as a: a.write(resp)
    title = re.search("<h1 class=\"title\">.+?</h1>", resp)
    if title:
        result["title"] = title.group(0).replace("<h1 class=\"title\">", "").replace("</h1>", "")
    
    summary = re.search("<div id=\"summary\">.+?</div>", resp, re.DOTALL)
    if not summary:
        summary = re.search("<p class=\".*?review\">.+?</p>", resp, re.DOTALL)
        if summary:
            repl = re.search("<p class=\".*?review\">", summary.group(0))
            result["summary"] = summary.group(0).replace(repl.group(0), "").replace("</p>", "").strip()
    else:
        repl = re.search("<div id=\"summary\">", summary.group(0))
        result["summary"] = summary.group(0).replace(repl.group(0), "").replace("</div>", "").strip()
    repl = re.search("<span.+?showMoreLessContentElement.+?>", result["summary"])
    if repl:
        result["summary"] = result["summary"].replace(repl.group(0), "").replace("</span>", "")
        repl = re.search("<span.+?showMoreLessControlElement.+", result["summary"], re.DOTALL)
        result["summary"] = result["summary"].replace(repl.group(0), "").strip()
        
    imgUrl = re.search("<img class=\"cover\".+?/>", resp)
    if imgUrl:
        repl = re.search("src=\".+?jpg", imgUrl.group(0))
        result["bookimg"] = "http:"+repl.group(0).replace("src=\"", "")
    
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
        print(True)
        isbn = isbn13to10(isbn)
    return isbn

def amazonInfo(isbn):
    '''
    Get the Amazon review for each book in books[]
    '''
    image = review = ''
    results = {}
    url = 'http://www.amazon.com/gp/product/' + str(isbn)
    br.open(url)
    html = br.response.content
    
    try:
        tpat = re.compile(r'<span id="productTitle" class="a-size-extra-large">(.*?)</span>')
        results['title'] = tpat.findall(html)[0]
        
        ipat = re.compile(r'data-a-dynamic-image="{&quot;(.*?)&quot;')
        results['image'] = ipat.findall(html)[0]

        rpat = re.compile('<noscript>(.*?)</noscript>', re.DOTALL)
        review = rpat.findall(html)[1]
        results['review'] = html2bbcode(review)

        return results
    except IndexError as e:
        #no results for this ISBN
        return results    

def html2bbcode(html):
    parser = HTML2BBCode()
    bbcode = str(parser.feed(str(html)))
    return bbcode


def sanitizeFilename(filename):
    '''Cleans up a filename to remove unallowed characters'''
    allowedSymbols = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0987654321.-_ ()[]+,~"
    newFilename = filename.split(".")[0]
    for symbol in filename:
        if (symbol not in allowedSymbols):
            newFilename = newFilename.replace(symbol, "")
    if (len(newFilename) > 47):
        newFilename = newFilename[:46].strip()
    newFilename = newFilename.replace(" ", "_")+".pdf"
    return newFilename

def generateBBCode(upUrl, info, filename):
    if (info["summary"] is ""): info["summary"] = "No summary :/"
    return "%s\n\n[img]%s[/img]\n\n[quote]%s[/quote]\n\nDownload: [url=%s]%s[/url]"\
                    % (info["title"], info["bookimg"], info["summary"], upUrl, filename)

def getBooksIndex():
    secInAweek = 604800
    indexfile = 'books_index.txt'
    #this nonsense here is to notgrab the index everytime, thewormkill doesn't update it that much.
    #feel free to coment out this try block if you need it updated everytime.
    try:
        with open(indexfile, 'r') as f:
            last_update = f.readline().strip()
            next_update = last_update + secInAWeek
            seconds_now = time.mktime(time.localtime())
            if  next_update < int(seconds_now)
                return
    except:
        pass

    url='https://evilzone.org/wiki//index.php/The_big_ebook_index'
    br.open(url)
    html=br.response.content

    if os.path.exists(indexfile):
        os.remove(indexfile)

    with open('books_index.txt', 'w+') as f:
        f.write(time.mktime(time.localtime()))

    for link in br.find_all("a"):
        url = link.get("href")
        
        #dirty url elimination, damn you thewormkill
        #an lxml pattern could have been easy
        if url: 

            if url[0] is '#' or \
               url.startswith('/wiki') or \
               '//www.mediawiki.org/' in url or \
               url == 'https://evilzone.org/wiki//index.php?title=The_big_ebook_index&oldid=1775':
                continue
            title = link.text
            with open('books_index.txt', 'a+') as f:
                f.write(str((link.text).encode('utf-8'))+' , '+ str((url).encode('utf-8'))+'\n')

def convert2pdf(filename):
    #http://manual.calibre-ebook.com/cli/ebook-convert.html
    filenm, ext = os.path.splitext(filename)
    #if ext not '.pdf'
    try:
        process = Popen(['ebook-convert', filename, filenm+'.pdf'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
    except OSError:
        print('Error: Calibre\'s ebook-converter not installed.' \
                ' Please install Calibre and continue.',file=sys.stderr)
        sys.exit()

def copyfile(filename,folder):
    if not os.path.exists(folder):
        os.makedir(folder) 
    try:
        shutil.move(filename, "%s/"%folder)
    except:
        filenm, ext = os.path.splitext(filename)
        for num in range(1000):
            if (not os.path.exists("%/"%folder+filenm+str(num)+ext)):
                shutil.move(filename, "%s/"%folder+filenm+str(num)+ext)
                break

def writeBBcode(goodFilename, upUrl, info):
    #TODO: create folder to hold BBcode and delete as you upload
    #create file to hold the BBcode and file details
    if (os.path.exists(goodFilename[:-4]+".txt")):
        for num in range(1000):
            if (not os.path.exists(goodFilename[:-4]+str(num)+".txt")):
                goodFilename = goodFilename[:-4]+str(num)+".txt"
                break
    try:
        with open(goodFilename[:-4]+".txt", "w") as bbOut: 
            bbOut.write(generateBBCode(upUrl, info,goodFilename))
    except TypeError:
        with open(goodFilename[:-4]+".txt", "w") as bbOut: 
            bbOut.write(unicode(generateBBCode(upUrl, info, goodFilename), "utf-8"))

def isdupe(title):
    import ast

    #load book index into tuple of (title, url)
    #TODO: Need an efficient, fast way to do this, levenstein distance included.
    with open('books_index.txt', 'r') as f:
        #read line by line
        for line in f:
            book_tuple = ast.literal_eval(line)
            if title in book_tuple[0]:
                return True
        return False

@with_goto
def process_file(filename):
    #Converting PDF to Text to extract ISBN number.
    print ("Processing '%s'..." % filename)
    text = convertPdf(filename)
    isbns = re.findall('(?:[0-9]{3}-)?[0-9]{1,5}-[0-9]{1,7}-[0-9]{1,6}-[0-9]', text)

    if (len(isbns) > 0):
        isbn = clean_isbn(isbns[0])
        goodFilename = sanitizeFilename(filename)
        os.rename(filename, goodFilename)
        print ("Found ISBN: %s, extracting info..." % isbn)

        print('Getting Book Details from Worldcat....')
        info = worldcatInfo(isbn)
                
        if info['summary'] is '':
            print('Getting book details from Amazon...')
            info = amazonInfo(isbn)

        #have failed to get any info on this book, jump to No_ISBN
        #this is metaprogramming not native to python
        if info['summary'] is '':
            goto .isbn_no_info

        #Uploading the file to http://upload.evilzone.org
        print ("Uploading as '%s'...\n" % goodFilename)
        upUrl = ezup.fileupload(goodFilename)

        #make Uploaded dir to keep files that have been uploaded and processed.
        #copyfiles(goodFilename, 'Uploaded')
               
        #write BBcode
        writeBBcode(goodFilename, upUrl, info)
    else:
        label .isbn_no_info
        #This is for the books without ISBN detected.
        #copyfiles(goodFilename, 'NoISBN')
        print ("Didn't find ISBN in file '%s'\n" % goodFilename)


def main():
    cookies = login('', '')
    index = threading.Thread(target=getBooksIndex)
    index.start()

    for filename in os.listdir("."):
        filenm, ext = os.path.splitext(filename)
        if ext in extensions:
            if filename.endswith(".pdf")):
                if not index.isAlive() and not isdupe(filename):
                    process_file(filename)

        #file not pdf
        else:
            #TODO: insert success conversion check here and in function return parameters, true/false
            convert2pdf(filename)
            process_file(filename)

if __name__ == '__main__':
    main()
