#!/usr/bin/env python3

import os, sys, glob
from mutagen.flac import FLAC

if __name__ == "__main__":
    dir_name = sys.argv[1]
    empty_tags = set()
    for filename in glob.glob(dir_name+'/**/*.flac', recursive=True):
        path_rel = pathlib.PurePath(filename)
        if len(part_rel.parts) != 3:
            print(f'Invalid filestructure: {filename}')
        f = FLAC(filename)
        missing_tags = []
        expected_tags = ('artist', 'album', 'genre', 'title', 'tracknumber', 'date')
        for k in expected_tags:
            if not k in f:
                missing_tags.append(k)
        if len(missing_tags):
            print(f'{filename:60}\nMissing tags: ', end='')
            for i, tag in enumerate(missing_tags):
                print(f'{tag}', end='')
                if i < len(missing_tags)-1:
                    print(',', end='')
                else:
                    print()
        if len(f) == 0:
            path = os.path.dirname(filename)
            empty_tags.add(path)
    for item in sorted(empty_tags):
        print(item)
