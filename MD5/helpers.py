#! /usr/bin/python3

import sys,re,os.path, chardet, glob

# Return tuple consisting of hash and filename, or None
def split_hash_filename(line):
    pattern = re.compile("([0-9a-f]{32})(\s+\**)(.*)")
    m = re.search(pattern, line)
    if m:
        d = dict()
        d['hash'] = m.group(1)
        d['ws'] = m.group(2)
        d['file'] = m.group(3)
        return d

def open_and_decode_file(in_fname):

    with open(in_fname, 'rb', encoding=None) as in_f:
        raw_data = in_f.read()
        det = chardet.detect(raw_data)
        print('File {}, encoding: {} (confidence: {})'.format(in_fname, det['encoding'], det['confidence']))
        data = raw_data.decode(det['encoding'])
        return data

# Create a filelist from a string containing filenames or foldernames. Filenames are added as they are.
# Folders are searched for files, depending on the recursive flag, subfolders are searched as well, or ignored.
# This function is designed to be used with ArgumentParser, where the last argument
# is the list of files/folders as described above.
# Note that nargs must be used with the path argument to accept multiple arguments.
# e.g.:
#   parser.add_argument('path', nargs='+', help='Folder containing files, or single/multiple file(s)')

def create_filelist(args, file_ext=None, recursive=False):
    '''args is a list or single item containing files and/or paths.
    file_ext is a string specifiying the allowed file extensions.
    '''
    # Using set to prevent duplicates
    filelist = []
    for path in args:
        if os.path.isdir(path):
            print('Got path: ', path)
            # Path is a directory. Collect all files and add them
            # TODO if file_ext is None, don't filter files
            if file_ext:
                glob_patt = '{}/*.{}'.format(path, file_ext)
            else:
                if recursive:
                    glob_patt = '**/*'
                else:
                    glob_patt = '*'
            res = glob.glob(glob_patt, root_dir=path, recursive=recursive)
            for r in res:
                f = os.path.join(path, r)
                if os.path.isfile(f):
                    filelist.append(f)

        elif os.path.isfile(path):
            print('Got file: ', path)
            # Path is a single file
            filelist.append(path)
        else:
            print('Invalid path: {}'.format(path))

    # Convert to set and back to list to get rid of duplicates
    return list(set(filelist))


