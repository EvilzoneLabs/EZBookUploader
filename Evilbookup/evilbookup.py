#!/usr/bin/env python
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

import os
import threading
import sys
import argparse
import json

from lib import process_file, convert2pdf, login, log, login, getBooksIndex
import lib

def is_valid(parser,arg):
    """verify the validity of the given file. Never trust the End-User"""
    try:
        os.access(arg, os.R_OK)
    except IOError as e:
        parser.error("File %s: %s"%(arg,e))
    else:
        return arg

def main(arg):
    parser = argparse.ArgumentParser(description='Process, upload and Post books on Evilzone Forum.')
    parser.add_argument("-f", "--file", dest="filename", required=False,
                        help="Ebook to process, upload and post on Evilzone",
                        metavar="FILENAME",type=lambda x:is_valid(parser,x))
    parser.add_argument("-F", "--folder", required=False, type=lambda x:is_valid(parser,x),
                        help="Folder to get books from.")#lambda func to verify time format
	
    args = parser.parse_args()

    cookies = login()
    extensions = ['.pdf', '.epub', '.mobi', '.chm']
    getBooksIndex()
    try:
        with open(os.path.join(lib.evilbookup_folder, 'log.json'), 'r') as f:
           lib.booklog = json.load(f)
    except ValueError as e:
        pass

    def process(filename):
        filenm, ext = os.path.splitext(filename)
        if ext in extensions:
            if filename.endswith(".pdf"):
                #moved this check to lib.process_file(), because filesystem file name (might)
                # differs from real book publication name hence dupe fail positives.
                #dupe = isdupe(filename);print(dupe);exit()
                #if not dupe:
                #    process_file(filename)
                #else:
                #    print('\'{0}\' already exists as \'{1}\' @ {2} Skipping...'.format(filename, dupe[0], dupe[1]))
                process_file(filename)
            #file not pdf
            else:
                #TODO: insert success conversion check here and in function return parameters, true/false
                newfilename = convert2pdf(filename)   #change this return value to a path.
                process_file(newfilename)

    if args.filename:
        process(args.filename)
    elif args.folder:
        for filename in os.listdir(args.folder):
            process(filename)
    else:
        print("\nNo filename or folder specified, checking in current directory...")
        files = os.listdir('.')
        found_book = False
        for filename in files:
            filenm, ext = os.path.splitext(filename)
            if ext in extensions:
                found_book = True				
                process(filename)
        if not found_book:
            print('No BOOK found in current directory. Please specify a file or folder to process books from.')
            sys.exit()
			        

    #dump the log back to file, prolly updated or not
    with open(os.path.join(lib.evilbookup_folder, 'log.json'), "w") as f:
        json.dump(lib.booklog, f, indent=4)
        
    print("Books processing is DONE, please review the {} folder for the BBcode to post to Evilzone.org".format(lib.bbcodedir))
if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
