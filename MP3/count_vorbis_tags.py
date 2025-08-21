#!/bin/python3

import os, sys, glob
from mutagen.flac import FLAC

if __name__ == "__main__":
    dir_name = sys.argv[1]
    empty_tags = set()
    for filename in glob.glob(dir_name+'/**/*.flac', recursive=True):
        f = FLAC(filename)
        if len(f) == 0:
            path = os.path.dirname(filename)
            empty_tags.add(path)
    for item in empty_tags:
        print(item)
