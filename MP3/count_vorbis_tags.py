#!/usr/bin/env python3

import os, sys, glob
import pathlib
import math

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers, extract_tags

def collect_file_info(dir_name):
    file_info = []
    for filename in glob.glob(dir_name+'/**/*.*', recursive=True):
        _,ext = os.path.splitext(filename)
        if ext in ['.mp3', '.flac']:
            f = extract_tags.FileInfo(filename)
            file_info.append(f)
    return sorted(file_info)

def dump_all_tags(file_info):
    expected_tags = ['t_artist', 't_album', 't_track', 't_title', 't_genre', 't_date']
    # Determine field lengths
    f_len = {}
    for e in expected_tags:
        f_len[e] = 0
    for f in file_info:
        for i, tag in enumerate(expected_tags):
            f_len[tag] = max(f_len[tag], len(f[tag]))
    print(f_len)
    for f in file_info:
        for i, tag in enumerate(expected_tags):
            print(f'{f[tag]:{f_len[tag]}}', end='')
            if i < len(expected_tags)-1:
                print(',', end='')
            else:
                print()
    
def dump_missing_tags(file_info):
    empty_tags = set()
    print('Files with partially or fully empty tags:')
    for f in file_info:
        missing_tags = []
        expected_tags = ['t_artist', 't_album', 't_genre', 't_title', 't_track', 't_date']
        for k in expected_tags:
            if not k in f.get_tags() or f[k] == '':
                missing_tags.append(k)
        if len(missing_tags):
            print(f'{f.file_name:60}\nMissing tags: ', end='')
            for i, tag in enumerate(missing_tags):
                print(f'{tag}', end='')
                if i < len(missing_tags)-1:
                    print(',', end='')
                else:
                    print()
        # Collect files where all tags of interest are missing
        if missing_tags == expected_tags:
            path = os.path.dirname(f.file_name)
            empty_tags.add(path)
    print('Folders containing files with fully empty tags:')
    for item in sorted(empty_tags):
        print(item)

def print_usage_and_die():
    print("""Usage:
    -d <top_dir>     Dump all tags in given directory.
    -m <top_dir>     Dump missing tags for files in given directory.
    """)
    sys.exit(1)
    
if __name__ == "__main__":
    # Require at least one argument
    if len(sys.argv) < 3:
        print_usage_and_die()
    if sys.argv[1] == '-d' and len(sys.argv) == 3:
        file_info = collect_file_info(sys.argv[2])
        dump_all_tags(file_info)
    if sys.argv[1] == '-m' and len(sys.argv) == 3:
        file_info = collect_file_info(sys.argv[2])
        dump_missing_tags(file_info)
