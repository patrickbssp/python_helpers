
import sys, os, glob, shutil

def print_error_and_exit(msg, exit_code=1):
    print('Error:',msg,', exitting now')
    sys.exit(exit_code)
    
cwd = sys.argv[1]

cwd_split = cwd.split(os.sep)
cwd_split[0]+=os.sep

print('CWD: {}'.format(cwd_split))
num_path_comp = len(cwd_split)

print('elem: {}'.format(num_path_comp))

work_dir = os.path.join(*cwd_split[:num_path_comp-2])
cur_dir = os.path.join(*cwd_split[num_path_comp-2:])
print('{}'.format(work_dir))
print('{}'.format(cur_dir))
wav_dir = os.path.join(work_dir, '_wave')
wave_admin_dir = os.path.join(wav_dir, '_admin')
md5sum_dir = os.path.join(work_dir, 'md5sum')

print('wav_dir: {}'.format(wav_dir))

### check whether wave admin dir exists

if not os.path.exists(wav_dir):
    print_error_and_exit('{} does not exist'.format(wav_dir))
if not os.path.exists(wave_admin_dir):
    print_error_and_exit('{} does not exist'.format(wave_admin_dir))
if not os.path.exists(md5sum_dir):
    print_error_and_exit('{} does not exist'.format(md5sum_dir))
    
### check, whether we have all files required


req_files = ['Take1','Take2','Take1.md5','Take2.md5','wav.md5']

for f in req_files:
    if not os.path.exists(os.path.join(cwd, f)):
        print_error_and_exit('{} does not exist'.format(f))

### check number of wav files

wave_files = glob.glob(cwd+os.sep+'*.wav')
num_wave_files = len(wave_files)
if num_wave_files == 0:
    print_error_and_exit('no wave files')

### check that number of MP3s is equal to number of wave files

cwd_mp3 = os.path.join(cwd,'Take1')
mp3_files = glob.glob(cwd_mp3+os.sep+'*.mp3')
num_mp3_files = len(mp3_files)
if num_mp3_files != num_wave_files:
    print_error_and_exit('number of wave and MP3 files not identical')

### clean up redundant files

take2_dir = os.path.join(cwd,'Take2')

# 1. remove all files unter Take2

take2_files = glob.glob(take2_dir+os.sep+'*.mp3')
for f in take2_files:
    os.remove(os.path.join(take2_dir, f))

# 2. remove dir Take2

os.rmdir(take2_dir)

# 3. remove Take2.md5

os.remove(os.path.join(cwd,'Take2.md5'))

### rename MD5 files

artist = cwd_split[num_path_comp-2]
album = cwd_split[num_path_comp-1]
print('Artist: {}, Album: {}'.format(artist,album))

dest_mp3_md5sum = os.path.join(md5sum_dir,'{} -- {} (FH).md5'.format(artist, album))
dest_wav_md5sum = os.path.join(wave_admin_dir,'{} -- {} (EAC).md5'.format(artist, album))

os.rename(os.path.join(cwd, 'Take1.md5'),dest_mp3_md5sum)
os.rename(os.path.join(cwd, 'wav.md5'),dest_wav_md5sum)

### create dest folders for wave files

if not os.path.exists(os.path.join(wav_dir,artist)):
    os.mkdir(os.path.join(wav_dir,artist))

if not os.path.exists(os.path.join(wav_dir,artist,album)):
    os.mkdir(os.path.join(wav_dir,artist,album))

### move all wave files to wave folder

for f in wave_files:
    shutil.move(f, os.path.join(wav_dir,artist,album))

### move all MP3 files one level up

for f in mp3_files:
    shutil.move(f, cwd)
    
### now, remove Take1 folder

os.rmdir(os.path.join(cwd,'Take1'))

#    new_filename = os.path.join(wav_dir,artist,album,os.path.basename(f))
#    os.rename(os.path.join(cwd,f),new_filename)