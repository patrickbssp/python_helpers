#!/usr/bin/python3

# Note: this script will only work with the 'real' unrar, not the unrar_wrapper provided by opensuse-oss!

import sys, os, subprocess
import shutil

if __name__ == '__main__':
    file_list = []

    if len(sys.argv) != 2:
        print('Error: Invalid number of arguments.')
        sys.exit()

    fname = sys.argv[1]
    if os.path.isdir(fname):
        for dirpath, dirnames, filenames in os.walk(fname):
            for file in filenames:
                fname = os.path.join(dirpath, file)
                file_list.append(fname)

    elif os.path.isfile(fname):
        file_list.append(fname)

    file_list.sort()
    extensions = []
    for fname in file_list:
        ext = os.path.splitext(fname)[1][1:]
        if ext not in extensions:
            extensions.append(ext)
        extension[ext].append(fname)
        print("{} {}".format(fname, ext.lower()))
    print(extensions)

