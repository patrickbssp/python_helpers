#!/usr/bin/env python3

import argparse
import os, re
import sys
import glob
import pathlib
from mutagen.id3 import ID3
from mutagen.flac import FLAC

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

def print_set(s):
    for i in sorted(s):
        print(i)

def compile_worklist(mp3_dir, flac_dir):
    
    mp3_dirs = set()
    flac_dirs = set()
    # Search for all MP3s and extract their Artist/Album path parts
    for filename in glob.glob(mp3_dir+'/**/*.mp3', recursive=True):
        p_dir = pathlib.PurePath(filename).parts[-3:-1]
        mp3_dirs.add(str(pathlib.PurePosixPath(*p_dir)))

    # Search for all FLACs and extract their Artist/Album path parts
    for filename in glob.glob(flac_dir+'/**/*.flac', recursive=True):
        p_dir = pathlib.PurePath(filename).parts[-3:-1]
        flac_dirs.add(str(pathlib.PurePosixPath(*p_dir)))

    return mp3_dirs, flac_dirs

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('mp3_dir', help='MP3 folder.')
    parser.add_argument('flac_dir', help='FLAC folder.')

    args = parser.parse_args()

    if not os.path.isdir(args.mp3_dir) or not os.path.isdir(args.flac_dir):
        print("Both arguments must be directories.")
        sys.exit(1)

    mp3_dirs, flac_dirs = compile_worklist(args.mp3_dir, args.flac_dir)
        
    print('MP3:')
    print(mp3_dirs)
    print('FLAC:')
    print(flac_dirs)
    print('common:')
    common = mp3_dirs & flac_dirs
    print_set(common)
    print('MP3 only')
    mp3_only = mp3_dirs - common
    print_set(mp3_only)
