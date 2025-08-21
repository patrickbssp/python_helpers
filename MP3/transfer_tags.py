#!/usr/bin/env python3

import argparse
import os, re
import sys
from mutagen.id3 import ID3
from mutagen.flac import FLAC
import pathlib

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

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

    try:
        flac_file = FLAC(flac_path)
    except Exception as e:
        print(f"Error reading {flac_path}: {e}")
        return

    print(f"Transferring tags\nfrom: {mp3_path}\nto:   {flac_path}")
    flac_size, flac_md5 = helpers.file_size(flac_path), helpers.file_md5(flac_path)
    for frame_id, frame_data in mp3_tags.items():
        vorbis_field = FRAME_MAP.get(frame_id, frame_id.lower())
        if verbose:
            print(f'{frame_id:10} -> {vorbis_field:12}: {frame_data}')
            
        val = frame_data.text[0]
        if vorbis_field == 'comment' and val == 'Digital Qual. 9':
            continue

        flac_file[vorbis_field] = str(val)

    if not verbose:
        print('{};{};{};{};{};{}'.format(
            flac_file['tracknumber'][0],
            flac_file['title'][0],
            flac_file['album'][0],
            flac_file['artist'][0],
            flac_file['date'][0],
            flac_file['genre'][0]))
  
    if not dry_run:
        try:
            flac_file.save()
        except Exception as e:
            print(f'Error saving {flac_path}: {e}')
    flac_size_new, flac_md5_new = helpers.file_size(flac_path), helpers.file_md5(flac_path)
    if flac_size_new != flac_size:
        print(f'Filesize has changed from {flac_size} to {flac_size_new}')
    print('{:14} {:9} {}'.format('FLAC before', flac_size, flac_md5))
    print('{:14} {:9} {}'.format('FLAC after', helpers.file_size(flac_path), helpers.file_md5(flac_path)))
    print('{:14} {:9} {}'.format('MP3', helpers.file_size(mp3_path), helpers.file_md5(mp3_path)))

def transfer_tags_dir(mp3_dir, flac_dir,dry_run=False, verbose=False):
    # Collect MP3 files
    mp3_files = []
    mp3_track_nr = set()
    flac_files = []
    flac_track_nr = set()
    for root, _, files in os.walk(mp3_dir):
        for file in files:
            if file.lower().endswith(".mp3"):
                mp3_files.append(file)
            else:
                print(f"Found non-conforming file {file}")

    for root, _, files in os.walk(flac_dir):
        for file in files:
            if file.lower().endswith(".flac"):
                flac_files.append(file)
            else:
                print(f"Found non-conforming file {file}")

    # Sanity checks. Verify that both folders have the same number of files,
    # and that all track number only occur once

    mp3_files = sorted(mp3_files)
    flac_files = sorted(flac_files)

    mp3_cnt = len(mp3_files)
    flac_cnt = len(flac_files)

    mp3_track_nr = get_track_numbers(mp3_files)
    flac_track_nr = get_track_numbers(flac_files)

    if mp3_track_nr != flac_track_nr:
        print('Track numbers do not match')
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

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', action='store_true', help='Dry-run only, do not change any files.')
    parser.add_argument('-v', action='store_true', help='Verbose logging.')
    parser.add_argument('mp3_dir', help='MP3 folder.')
    parser.add_argument('flac_dir', help='FLAC folder.')
    
    args = parser.parse_args()
    
    if not os.path.isdir(args.mp3_dir) or not os.path.isdir(args.flac_dir):
        print("Both arguments must be directories.")
        sys.exit(1)

    transfer_tags_dir(args.mp3_dir, args.flac_dir, args.d, args.v)

