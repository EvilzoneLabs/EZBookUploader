import os
import threading
import sys
import argparse
import json

from lib import process_file, convert2pdf, login, isdupe, log, login, getBooksIndex
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

    cookies = login('nafuti', 'Emmanuel1')
    extensions = ['.pdf', '.epub', 'mobi', 'chm']
    #index = threading.Thread(target=getBooksIndex)
    #index.start()
    getBooksIndex()
    try:
        with open(os.path.join(lib.ezbookup_folder, 'log.json'), 'r') as f:
           lib.booklog = json.load(f)
    except ValueError as e:
        pass

    def process(filename):
        filenm, ext = os.path.splitext(filename)
        if ext in extensions:
            if filename.endswith(".pdf"):
                dupe = isdupe(filename)
                if not dupe:
                    process_file(filename)
                else:
                    print('\'{0}\' already exists as \'{1}\' @ {2} Skipping...'.format(filename, dupe[0], dupe[1]))
            #file not pdf
            else:
                #TODO: insert success conversion check here and in function return parameters, true/false
                convert2pdf(filename)
                process_file(filename)

    if args.filename:
        process(args.filename)
    elif args.folder:
        for filename in os.listdir(args.folder):
            process(filename)
    else:
        files = os.listdir('.')
        if not files:
            print('NO file or folder specified and NONE found in'
                  +' current directory. Please specify a file or folder to process books from.')
            sys.exit()
        for filename in os.listdir('.'):
            process(filename)

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
