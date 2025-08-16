#!/usr/bin/env python3

import os, re
import sys
from mutagen.id3 import ID3
from mutagen.flac import FLAC

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


def transfer_tags(mp3_path, flac_path):
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

    print(f"Transferring tags from: {mp3_path}\nto: {flac_path}")
    for frame_id, frame_data in mp3_tags.items():
        vorbis_field = FRAME_MAP.get(frame_id, frame_id.lower())
        print(f'{frame_id:10} -> {vorbis_field:12}: {frame_data}')
            
        val = frame_data.text[0]
        if vorbis_field == 'comment' and val == 'Digital Qual. 9':
            print(f'Ignoring text: {val}')
            return

        flac_file[vorbis_field] = str(val)

    try:
        flac_file.save()
    except Exception as e:
        print(f"Error saving {flac_path}: {e}")

def transfer_tags_dir(mp3_dir, flac_dir):
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
    print(f'Number of MP3 files: {mp3_cnt}')
    print(f'Number of FLAC files: {flac_cnt}')

    mp3_track_nr = get_track_numbers(mp3_files)
    flac_track_nr = get_track_numbers(flac_files)

    if mp3_track_nr != flac_track_nr:
        print('Track numbers do not match')
        return

    track_cnt = len(mp3_track_nr)
    print(f'Number of track numbers: {track_cnt}')

    if mp3_cnt != flac_cnt != track_cnt:
        print('Mismatch of number of files and number of tracks')
        return

    # Iterate over track numbers and get files pair-wise
    for i in range(mp3_cnt):
        transfer_tags(os.path.join(mp3_dir, mp3_files[i]), os.path.join(flac_dir, flac_files[i]))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python transfer_tags.py <mp3_directory> <flac_directory>")
        sys.exit(1)

    mp3_dir = sys.argv[1]
    flac_dir = sys.argv[2]

    if not os.path.isdir(mp3_dir) or not os.path.isdir(flac_dir):
        print("Both arguments must be directories.")
        sys.exit(1)

    transfer_tags_dir(mp3_dir, flac_dir)

