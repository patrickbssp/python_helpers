#!/usr/bin/env python3

import argparse
import os
import re
import sys
import pathlib
from mutagen.id3 import ID3
from mutagen.flac import FLAC
from mutagen import MutagenError

# Mapping from ID3 frame to Vorbis comment field
#    "TPOS": "discnumber",
#    "TCON": "genre",
#    "TYER": "date",
#    "TDRC": "date",
#    "COMM": "comment",
#    "COMM::eng": "comment",



class FileInfo():
    file_name = ''
    # Tags from ID3 or Vorbis meta data
    t_tags = {
        't_track'        : { 'id3' : 'TRCK', 'vorbis' : 'tracknumber'},
        't_artist'       : { 'id3' : 'TPE1', 'vorbis' : 'artist'},
        't_album_artist' : { 'id3' : 'TPE2', 'vorbis' : 'albumartist'},
        't_album'        : { 'id3' : 'TALB', 'vorbis' : 'album'},
        't_title'        : { 'id3' : 'TIT2', 'vorbis' : 'title'},
        't_date'         : { 'id3' : 'TDRC', 'vorbis' : 'date'},
        't_genre'        : { 'id3' : 'TCON', 'vorbis' : 'genre'},
    }
    # Tags from file/path
    f_tags = {
        'f_artist',
        'f_album',
        'f_title',
        'f_track'
    }
    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __getitem__(self, key):
        return str(getattr(self, key))

    def __get_file_info__(self, file):

        self.file_name = file

        path_parts = pathlib.PurePath(file).parts
        basename = path_parts[-1]
        if len(path_parts) >= 3:
            self['f_artist'] = path_parts[-3]
            self['f_album'] = path_parts[-2]

        m = re.search(r'(\d\d) - (.*)\.(mp3|flac)', basename)
        if m:
            self['f_track'] = m.group(1)
            self['f_title'] = m.group(2)
            self['f_type'] = m.group(3)
        else:
            m = re.search(r'Track(\d\d)\.(mp3|flac)', basename)
            if m:
                self['f_track'] = m.group(1)
                self['f_type'] = m.group(2)

    def __lt__(self, other):
        '''
            Sort function, first compare by artist, then album, and then track number
        '''
        return (self['t_artist'], self['t_album'], self['t_track']) < (other['t_artist'], other['t_album'], other['t_track'])
                    
    def __init__(self, file):
        '''Extract tags from MP3 or FLAC file.'''
        for tag in self.f_tags:
            self[tag] = ''

        for tag in self.t_tags.keys():
            self[tag] = ''

        self.__get_file_info__(file)
        
        if self.f_type == 'mp3':
            try:
                mp3_tags = ID3(file)
            except MutagenError as e:
                print(f"Error reading {file}: {e}")
                return

            for tag in self.t_tags:
                id3 = self.t_tags[tag]['id3']
                if id3 in mp3_tags:
                    self[tag] = mp3_tags[id3]

        elif self.f_type == 'flac':
            try:
                flac_tags = FLAC(file)
            except MutagenError as e:
                print(f"Error reading {file}: {e}")
                return

            for tag, vals in self.t_tags.items():
                v = vals['vorbis']
                if v in flac_tags:
                    self[tag] = flac_tags[v][0]

    def dump(self):
        str1 = f'File: {self['f_track']}, {self['f_title']}, type: {self['f_type']}'
        str2 = f'Tag:  {self['t_track']}, {self['t_title']}, {self['t_artist']}, {self['t_album']}, {self['t_genre']}, {self['t_date']}'
        print(f'{str1}\n{str2}')

    def get_tags(self):
        return self.t_tags

    def save(self):
        if self.f_type == 'mp3':
            print('Not implemented yet.')
        elif self.f_type == 'flac':
            try:
                flac_tags = FLAC(self.file_name)
            except MutagenError as e:
                print(f"Error reading {self.file_name}: {e}")
                return

#            print(self.t_tags)
#            print(self.t_tags.items())
            for tag, vals in self.t_tags.items():
                print(f'tag: {tag}, v: {vals}')
                v = self[tag]
                if len(v) > 0:
                    print(f'got tag: {tag}, v: {v}')
             #       flac_tags[tag][0] = v
            print(f'Saving file: {self.file_name}')
    #        flac_tags.save()
            
def read_csv(csv_file):
    '''Read CSV file and store contents in FileInfo objects
    '''
    ### Open CSV file
    with open(csv_file, mode='r', encoding='utf-8', errors='surrogateescape') as csv_fh:
        csv_wh = csv.DictReader(csv_fh, fieldnames=field_names, dialect='mp3_csv')
        csv_wh.writeheader()

        for full_path in files:
            fi = extract_tags.FileInfo(full_path)
            tag = tag_from_fileinfo(fi, field_names)
            csv_wh.writerow(tag)
    
if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('file_name', help='MP3 or FLAC file name.')

    args = parser.parse_args()

    if not os.path.isfile(args.file_name):
        print("Argument must be a file.")
        sys.exit(1)

    tags = FileInfo(args.file_name)
    tags.dump()
