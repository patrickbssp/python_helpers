#!/usr/bin/python3

'''
This script combines the functionality of the former comp_sums.sh shell script
and the python script splitter.py.

This script expects two sets of MP3 files in the folders Take1 and Take2 in the
work directory (CWD), as well as the wave files in CWD.

For both sets of MP3 files, the MD5 hashes are generated and compared.
Also, for the wave files the hashes are compared.

If the MP3 hashes match and the number of files matches, the hashes are dumped to
files, named after the artist and album.

From the MP3 files, only one set is kept and moved to the proper place. The wave
files are moved to a specific directory as well.

The script expects the following directory structure:

/path/to/workdir/Artist/Album (CWD, argument to script)
/path/to/workdir              (workdir)
/path/to/workdir/_wave        (destination for wave files)
/path/to/workdir/_wave/_admin (destination for wave files MD5 hash file)
/path/to/workdir/md5sum       (destination for MP3 files MD5 hash file)

The script creates the following directories:

/path/to/workdir/_wave/Artist/Album   (destination for current wave files)

'''

import sys, os, glob, shutil
import re
import shlex
import subprocess
import pathlib

# custom modules
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

wav_pattern = r'.*\.wav'
mp3_pattern = r'.*\.mp3'

def print_error_and_exit(msg, exit_code=1):
    print('Error: {}, exitting now'.format(msg))
    sys.exit(exit_code)

def collect_hashes(dir, pattern):
    files = [f for f in os.listdir(dir) if re.match(pattern, f)]
    hashes = {}
    for f in files:
        md5 = file_md5(os.path.join(dir, f))
        # Add dict entry
        hashes[f] = md5
    return hashes

def dump_hashes(md5_file, hashes):
    with open(md5_file, mode='w+', encoding='utf-8') as f:
        for k in sorted(hashes.keys()):
            f.write("{}  {}\n".format(hashes[k], k))

def move_files(dest_dir, src_dir, pattern):
    files = [f for f in os.listdir(src_dir) if re.match(pattern, f)]
    for f in files:
        print('Moving file {} to {}'.format(os.path.join(src_dir, f), dest_dir))
        shutil.move(os.path.join(src_dir, f), dest_dir)

def delete_directory(dir):
    print('Deleting directory {}'.format(dir))
    shutil.rmtree(dir)

if len(sys.argv) != 2:
    print_error_and_exit('No argument given')

cwd = sys.argv[1]
if not os.path.exists(cwd):
    print_error_and_exit('Argument is no valid directory')

hashes = []

for f in ['Take1','Take2']:
    dir = os.path.join(cwd, f)
    if not os.path.exists(dir):
        print_error_and_exit('{} does not exist'.format(dir))
    new_hashes = collect_hashes(dir, mp3_pattern)
    if len(new_hashes) == 0:
        print_error_and_exit('No files in {}'.format(dir))
    hashes.append(new_hashes)

if(hashes[0] != hashes[1]):
    print('Hashes T1 ({} files):'.format(len(hashes[0])))
    print(hashes[0])
    print('Hashes T2 ({} files):'.format(len(hashes[1])))
    print(hashes[1])
    print_error_and_exit('Hashes do not match.')
else:
    print('Hashes match ({} files each)'.format(len(hashes[0])))
    for k in hashes[0].keys():
        print(k, hashes[0][k])

# Collect hashes for wave files
wav_hashes = collect_hashes(cwd, wav_pattern)
print('Got {} wave files'.format(len(wav_hashes)))
for k in wav_hashes.keys():
    print(k, wav_hashes[k])

###############################

cwd_split = cwd.split(os.sep)
cwd_split[0]+=os.sep

### Get rid of trailing '/' if existent
if len(cwd_split[-1]) == 0:
    cwd_split = cwd_split[:-1]

print('CWD: {}'.format(cwd_split))
artist = cwd_split[-2]
album = cwd_split[-1]
print('Artist: {}, Album: {}'.format(artist,album))

work_dir = os.path.join(*cwd_split[:-2])
print('work_dir: {}'.format(work_dir))

wav_dir = os.path.join(work_dir, '_wave')
wave_admin_dir = os.path.join(wav_dir, '_admin')
md5sum_dir = os.path.join(work_dir, 'md5sum')

print('wav_dir: {}'.format(wav_dir))
print('wave_admin_dir: {}'.format(wave_admin_dir))
print('md5sum_dir: {}'.format(md5sum_dir))

### check whether all required directories exist

if not os.path.exists(wav_dir):
    print_error_and_exit('Wave dir does not exist: {}'.format(wav_dir))
if not os.path.exists(wave_admin_dir):
    print_error_and_exit('Wave admin dir does not exist: {}'.format(wave_admin_dir))
if not os.path.exists(md5sum_dir):
    print_error_and_exit('md5sum dir does not exist: {}'.format(md5sum_dir))

### Check number of hashes
num_mp3_hashes = len(hashes[0])
num_wav_hashes = len(wav_hashes)

if num_mp3_hashes == 0:
    print_error_and_exit('No MP3 hashes available')
elif num_wav_hashes == 0:
    print_error_and_exit('No Wave hashes available')
elif num_mp3_hashes != num_wav_hashes:
    print_error_and_exit('number of wave and MP3 files not identical')
else:
    print('Number of hashes:{}'.format(num_mp3_hashes))

### Write hashes to files
dump_hashes(os.path.join(md5sum_dir, '{} -- {} (FH).md5'.format(artist, album)), hashes[0])
dump_hashes(os.path.join(wave_admin_dir, '{} -- {} (EAC).md5'.format(artist, album)), wav_hashes)

### create dest folder for wave files and move wave files there
dest_dir = os.path.join(wav_dir,artist,album)
os.makedirs(dest_dir, exist_ok=True)
move_files(dest_dir, cwd, wav_pattern)

### Move files from Take1 one level up and then delete folders Take1 and Take2
move_files(cwd, os.path.join(cwd, 'Take1'), mp3_pattern)
delete_directory(os.path.join(cwd, 'Take1'))
delete_directory(os.path.join(cwd, 'Take2'))

print('Done')
sys.exit(0)
