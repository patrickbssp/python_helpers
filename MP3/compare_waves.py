#!/bin/python3

import sys, os
import shlex
import subprocess, shlex
#import scipy as sp
from scipy.io import wavfile
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np

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

class wave_obj:

    def __init__(self, filename):
        # data: audio data in a 2-dim array
        # sample_cnt: number of samples (one channel)
        # channel_cnt: number of samples (one channel)
        self.filename = filename
        self.filesize = os.path.getsize(filename)
        self.sample_rate, self.data = wavfile.read(filename)
        self.sample_cnt, self.channel_cnt = self.data.shape
        self.time = self.sample_cnt/44.1e3
        self.md5 = file_md5(filename)

    def dump(self):
        print('filename: {}'.format(self.filename))
        print('size: {}'.format(self.filesize))
        print('MD5: {}'.format(self.md5))
        print('samples: {}'.format(self.sample_cnt))
        print('channels: {}'.format(self.channel_cnt))
        print('duration: {}'.format(self.time))

# Calculate the squared difference of two arrays
def delta_sum(a1, a2):
    d = a1 - a2
    return np.sum(d**2)

# Compare two waveforms
# Return value:
#   None: Waveforms don't match at all
#   0:      Waveforms match perfectly
#   != 0:   Waveforms match with an offset
def compare_waveforms(w1, w2):
    if len(w1) != len(w2):
        # no match (length mismatch)
        return None
    if delta_sum(w1, w2) == 0:
        # match without offset
        return 0

    p1 = find_peaks(w1)
    p2 = find_peaks(w2)
    o = p2[0][0] - p1[0][0]

    # Shift waveforms
    w2_s = np.roll(w2, -o)
    if delta_sum(w1, w2_s) == 0:
        # match with offset
        return o
    else:
        # no match
        return None


if len(sys.argv) != 3:
    print('missing input file(s)')
    sys.exit(0)

w1 = wave_obj(sys.argv[1])
w1.dump()
w2 = wave_obj(sys.argv[2])
w2.dump()

ret_l = compare_waveforms(w1.data[:,0], w2.data[:,0])
ret_r = compare_waveforms(w1.data[:,1], w2.data[:,1])

if ret_l == 0 and ret_r == 0:
    print('Perfect match')
elif ret_l == None or ret_r == None:
    print('No match')
else:
    print('Match with offsets: {} / {}'.format(ret_l, ret_r))




# Plot data
time = np.linspace(0, w1.sample_cnt, w1.sample_cnt)

#plt.plot(time, dl, label='Delta Left', color='red')
#plt.plot(time, dr, label='Delta Right', color='blue')
#plt.show()
