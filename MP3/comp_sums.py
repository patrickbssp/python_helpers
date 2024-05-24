#!/usr/bin/python3

import sys, os, glob, shutil
import re
import shlex
import subprocess

### strip trailing newline and convert to UTF-8
def strip_shell(txt):
    return txt[:-1].decode('utf-8')

def file_md5(file):
    cmd = '/usr/bin/md5sum "{}"'.format(file)
    args = shlex.split(cmd)
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    txt = strip_shell(p.stdout.read())
    md5 = txt.split()[0]
    return md5

def print_error_and_exit(msg, exit_code=1):
    print('Error: {}, exitting now'.format(msg))
    sys.exit(exit_code)
    

def collect_hashes(dir):
    files = [f for f in os.listdir(dir) if re.match(r'[0-9]+.*\.mp3', f)]
    hashes = {}
    for f in files:
        md5 = file_md5(os.path.join(dir, f))
        # Add dict entry
        hashes[f] = md5
    return hashes

if len(sys.argv) != 2:
    print_error_and_exit('No argument given')

cwd = sys.argv[1]
if not os.path.exists(cwd):
    print_error_and_exit('Argument is no valid directory')

req_files = ['Take1','Take2']
hashes = []

for f in req_files:
    dir = os.path.join(cwd, f)
    if not os.path.exists(dir):
        print_error_and_exit('{} does not exist'.format(dir))
    new_hashes = collect_hashes(dir)
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

print('Done')
sys.exit(0)
