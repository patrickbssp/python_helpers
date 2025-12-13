#!/usr/bin/env python3

import argparse
import os, re
import sys
import glob
import pathlib
from mutagen.id3 import ID3
from mutagen.flac import FLAC

# Todo
#
# Write function to extract tags from CSV file instead of a file.
# Then, provide functions to identify file info instances based on search criteria
# like Album, Artist, Track number etc.

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers, extract_tags

# Mapping from ID3 frame to Vorbis comment field
FRAME_MAP = {
    "TPE1": "artist",
    "TPE2": "albumartist",
    "TALB": "album",
    "TIT2": "title",
    "TRCK": "tracknumber",
    "TPOS": "discnumber",
    "TCON": "genre",
    "TYER": "date",
    "TDRC": "date",
    "COMM": "comment",
    "COMM::eng": "comment",
}

def get_track_numbers(file_list):
    '''Get track numbers from file list.

    This function detects, whether the file list contains MP3 files in the format xx - Title.mp3,
    or FLAC files in the format Trackxx.flac.
    '''
    nr_set = set()
    for file in file_list:
        m = re.search(r'^([0-9]*).*mp3', file)
        if m:
            nr_set.add(m.group(1))
        else:
            m = re.search(r'Track([0-9]*)\.flac', file)
            if m:
                nr_set.add(m.group(1))
    return nr_set


def transfer_tags(mp3_path, flac_path, dry_run=False, verbose=False):
    '''Copy ID3 tags from a MP3 file and save them to as Vorbis comments to a FLAC file.'''
    print('----------------------------------------------------------------------------------------')
    try:
        mp3_tags = ID3(mp3_path)
    except Exception as e:
        print(f"Error reading {mp3_path}: {e}")
        return

    mp3_file = extract_tags.FileInfo(mp3_path)
    flac_file = extract_tags.FileInfo(flac_path)

    print(f"Transferring tags\nfrom: {mp3_path}\nto:   {flac_path}")
    flac_size, flac_md5 = helpers.file_size(flac_path), helpers.file_md5(flac_path)

    # Copy fields from MP3 file to FLAC file
    for id in extract_tags.FileInfo.t_tags:
        print(id)
        id3_tag = extract_tags.FileInfo.t_tags[id]['id3']
        print(f'Copying {id}: {mp3_file[id]} ({id3_tag})')
    
    for frame_id, frame_data in mp3_tags.items():
        vorbis_field = FRAME_MAP.get(frame_id, frame_id.lower())
        if verbose:
            print(f'{frame_id:10} -> {vorbis_field:12}: {frame_data}')

        val = frame_data.text[0]
        if vorbis_field == 'comment' and val == 'Digital Qual. 9':
            continue

        flac_file[vorbis_field] = str(val)

    if not verbose:
        try:
            date = flac_file['date'][0]
        except KeyError:
            date = ''
        print('{};{};{};{};{};{}'.format(
            flac_file['tracknumber'],
            flac_file['title'],
            flac_file['album'],
            flac_file['artist'],
            date,
            flac_file['genre']))

    if not dry_run:
        try:
            flac_file.save()
        except Exception as e:
            print(f'Error saving {flac_path}: {e}')
    flac_size_new, flac_md5_new = helpers.file_size(flac_path), helpers.file_md5(flac_path)
    if flac_size_new != flac_size:
        print(f'Filesize has changed from {flac_size} to {flac_size_new}')
    print(f'FLAC before {flac_size:9} {flac_md5}')
    print(f'FLAC after  {flac_size_new:9} {flac_md5_new}')
    print(f'MP3         {helpers.file_size(mp3_path):9} {helpers.file_md5(mp3_path)}')

def transfer_tags_dir(mp3_dir, flac_dir,dry_run=False, verbose=False):
    '''Transfer tags from MP3 files to FLAc files.

    This function expects a path to a folder containing MP3 files, where the last 2 directory components
    are expected to be Artist and Album. The same applies for the FLAC folder. The function checks,
    whether the number of tracks is the same as a simple safe-guard to mismatches.

    Behaviour can be controlled by switches dry_run, and verbose.
    '''
    # Collect MP3 files
    mp3_files = []
    mp3_track_nr = set()
    flac_files = []
    flac_track_nr = set()
    for _, _, files in os.walk(mp3_dir):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(file)
            else:
                print(f"Found non-conforming file {file}")

    for _, _, files in os.walk(flac_dir):
        for file in files:
            if file.lower().endswith(".flac"):
                flac_files.append(file)
            else:
                print(f"Found non-conforming file {file}")

    # Sanity checks. Verify that both folders have the same number of files,
    # and that all track number only occur once

    mp3_files = sorted(mp3_files)
    flac_files = sorted(flac_files)

    print(mp3_files)
    print(flac_files)

    print(mp3_dir)
    print(flac_dir)

    mp3_cnt = len(mp3_files)
    flac_cnt = len(flac_files)

    mp3_track_nr = sorted(get_track_numbers(mp3_files))
    flac_track_nr = sorted(get_track_numbers(flac_files))

    if mp3_track_nr != flac_track_nr:
        print(f'Track numbers do not match. MP3: {mp3_track_nr}, FLAC: {flac_track_nr}')
        return

    track_cnt = len(mp3_track_nr)

    if mp3_cnt != flac_cnt != track_cnt:
        print('Mismatch of number of files and number of tracks')
        print(f'Number of MP3 files: {mp3_cnt}')
        print(f'Number of FLAC files: {flac_cnt}')
        print(f'Number of track numbers: {track_cnt}')
        return

    # Iterate over track numbers and get files pair-wise
    for i in range(mp3_cnt):
        mp3_path = os.path.join(mp3_dir, mp3_files[i])
        flac_path = os.path.join(flac_dir, flac_files[i])
        transfer_tags(mp3_path, flac_path, dry_run, verbose)


def compile_worklist(mp3_dir, flac_dir):
    
    all_dirs = set()
    # Search for all MP3s and extract their Artist/Album path parts
    for filename in glob.glob(mp3_dir+'/**/*.mp3', recursive=True):
        p_dir = pathlib.PurePath(filename).parts[-3:-1]
        all_dirs.add(pathlib.PurePosixPath(*p_dir))

    work_list = []

    for dir in all_dirs:
        # Create FLAC path and check whether it exists
        flac_p = f'{flac_dir}/{dir}'
        mp3_p = f'{mp3_dir}/{dir}'
        if os.path.exists(flac_p):
            work_list.append((mp3_p, flac_p))
    return work_list

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', action='store_true', help='Collection mode.')
    parser.add_argument('-d', action='store_true', help='Dry-run only, do not change any files.')
    parser.add_argument('-v', action='store_true', help='Verbose logging.')
    parser.add_argument('mp3_dir', help='MP3 folder.')
    parser.add_argument('flac_dir', help='FLAC folder.')

    args = parser.parse_args()

    if not os.path.isdir(args.mp3_dir) or not os.path.isdir(args.flac_dir):
        print("Both arguments must be directories.")
        sys.exit(1)

    if args.c:
        # Collection mode, assume that folders are start points for collections,
        # i.e. below the start point there will be two folders Artist and Album
        # below each other, and then containing either MP3 or FLAC files.
        #
        work_list = compile_worklist(args.mp3_dir, args.flac_dir)
        
        print(work_list)
        for p in work_list:
            print(f'{p[0]}\n{p[1]}\n')
            transfer_tags_dir(p[0], p[1], args.d, args.v)
    else:
        # Single album mode
        transfer_tags_dir(args.mp3_dir, args.flac_dir, args.d, args.v)
        
