#! /usr/bin/python3

import sys, re, os.path, chardet, glob, shlex, subprocess


### strip trailing newline and convert to UTF-8
def strip_shell(txt):
	return txt[:-1].decode('utf-8')

### Calculate MD5 hash of file, using md5sum
def file_md5(file):
	cmd = '/usr/bin/md5sum "{}"'.format(file)
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	txt = strip_shell(p.stdout.read())
	md5 = txt.split()[0]
	return md5

# Determine file type
def file_type(file):
	cmd = '/usr/bin/file -b "{}"'.format(file)
	args = shlex.split(cmd)
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	txt = strip_shell(p.stdout.read())
	return txt

def file_size(file):
	size = os.stat(file).st_size
	return size

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
    filelist = []
    for path in args:
        if os.path.isdir(path):
            # Path is a directory. Collect all files and add them
            file_patt = '*.{}'.format(file_ext) if file_ext else '*'
            glob_patt = '**/*{}'.format(file_patt) if recursive else '*{}'.format(file_patt)
            res = glob.glob(glob_patt, root_dir=path, recursive=recursive)
            for r in res:
                f = os.path.join(path, r)
                if os.path.isfile(f):
                    filelist.append(f)

        elif os.path.isfile(path):
            # Path is a single file
            filelist.append(path)
        else:
            print('Invalid path: {}'.format(path))

    # Convert to set and back to list to get rid of duplicates
    return list(set(filelist))


