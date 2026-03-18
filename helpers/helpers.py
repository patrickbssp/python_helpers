#! /usr/bin/python3

import sys, re, os.path, chardet, glob, shlex, subprocess, pathlib
import fnmatch

### strip trailing newline and convert to UTF-8
def strip_shell(txt):
	return txt[:-1].decode('utf-8')

### Calculate MD5 hash of file, using md5sum
def file_md5(file):
	args = shlex.split('/usr/bin/md5sum "{}"'.format(file))
	p = subprocess.Popen(args, stdout=subprocess.PIPE)
	return p.stdout.read().decode('utf-8').split()[0]

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
    pattern = re.compile(r"([0-9a-f]{32})(\s+\**)(.*)")
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


def check_ext(filename, filters=None):
    '''Check whether filename matches any filter in filters.

    Basically, the function is a wrapper for fnmatch, providing the
    option to check against multiple filters. Therefore, the matching
    rules are UNIX-like, not regular expressions.

    Return True if the file matches any filter, False otherwise.
    '''
    if not filters:
        # Nothing to compare against
        return True
    else:
        for filter in filters:
            if fnmatch.fnmatch(filename, filter):
                return True
    return False


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


def collect_files(src_path, use_recursion=None, use_filters=None, use_relpath=False):
    '''Collect files from path according to pattern.

    src_path        Path from where search should start.
    use_recursion   If True, descend into all sub-directories of src_path
    use_filters     A list of search filters to be considered, e.g. [*.wav, *.mp3], if ommited, all files are included
    use_relpath     If True, return filenames relative to path, otherwise return full paths
    use_sort        If True, return filenames sorted, otherwise return as-is

    Return a list of filenames.
    '''

    if not os.path.isdir(src_path):
        return None

    filelist = []

    # Path is a directory. Collect all files and add them
    print('==========================')
    for path, dirs,files in os.walk(src_path):
        for file in files:
            print('--------------------------')
            print(f'path: {path}')
            f = os.path.join(path, file)
            p_splitted = pathlib.Path(path).parts
            print(p_splitted)
            if not use_recursion and len(p_splitted) > 0:
                # In non-recursive mode, only add files in current dir
                pass
            else:
                if check_ext(file, use_filters):
                    print(file)
                    filelist.append(file)

    return sorted(filelist)
