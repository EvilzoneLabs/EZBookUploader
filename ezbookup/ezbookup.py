import os
import threading
from lib import process_file, convert2pdf, login, isdupe, log

def is_valid(parser,arg):
    """verify the validity of the given file. Never trust the End-User"""
    try:
        os.access(arg, os.R_OK)
    except IOError as e:
        parser.error("File %s: %s"%(arg,e))
    else:
        return arg

def process

def main(args):
    parser = argparse.ArgumentParser(description='Process, upload and Post books on Evilzone Forum.')
    parser.add_argument("-f", "--file", dest="filename", required=False,
                        help="Input code/text file to upload",
                        metavar="FILENAME",type=lambda x:is_valid(parser,x))
    parser.add_argument("-F", "--folder", required=False, type=lambda x:is_valid(parser,x),
                        help="Folder to get books from.")#lambda func to verify time format
	
    args = parser.parse_args()

    cookies = login('', '')
    extensions = ['.pdf', '.epub', 'mobi']
    index = threading.Thread(target=getBooksIndex)
    index.start()

    def process(filename):
        filenm, ext = os.path.splitext(filename)
        if ext in extensions:
            if filename.endswith(".pdf")):
                dupe = isdupe(filename)
                if not dupe:
                    process_file(filename)
                else:
                    print('\'{0}\' already exists as \'{1}\' @ {2} Skipping...'.format(filename, dupe[0], dupe[1]))
                    continue
            #file not pdf
            else:
                #TODO: insert success conversion check here and in function return parameters, true/false
                convert2pdf(filename)
                process_file(filename)

    if args.filename:
        process(args.filename)
    elif args.folder:
        for filename in os.listdir(args.folder):
        

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
