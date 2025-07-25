#!/bin/python3

import matplotlib as mp
#mp.use('Qt4Agg')
mp.use('TkAgg')

import sys, os
import shlex
import subprocess, shlex
#import scipy as sp
from scipy.io import wavfile
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np
import fnmatch

# custom modules
import pathlib
mod_path = pathlib.Path(__file__).resolve().parents[1]/'helpers'
sys.path.insert(0, str(mod_path))
import helpers

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
        self.md5 = helpers.file_md5(filename)

    def dump(self):
        print('filename: {}'.format(self.filename))
        print('MD5: {}'.format(self.md5))
        print('channels: {}, samples: {}, size: {}'.format(self.channel_cnt, self.sample_cnt, self.filesize))
        print('duration: {:.1f}'.format(self.time))

    def dump_short(self):
        print('{} {}'.format(self.md5, self.filename))
        print('channels: {}, samples: {}, bytes: {}, duration: {:.1f}'.format(self.channel_cnt, self.sample_cnt,
                self.filesize, self.time))

# Test pattern with 5 differing samples at the start only
test_pat_1 = [0,1,2,3,4]

# Test pattern with 5 differing samples at the end only
test_pat_2 = [296,297,298,299,300]

# Evalaute diff waveform
# Test whether differences are concentrated at either the beginning andf/or the end.
# Expact a list of indices of differing samples.
# I.e.: a the list [0,1,233,300] means, that 4 samples are differing, at the positions 0, 1, 233, and 300.
def evaluate_diff(diff, wave_len):
    MIN_TH = 16
    MAX_TH = 16
    bins = {'start':0, 'mid':0,'end':0}
    for d in diff:
        if d < 16:
            bins['start'] += 1
        elif d > wave_len-16:
            bins['end'] += 1
        else:
            bins['mid'] += 1
    return bins

# Calculate the squared difference of two arrays
def delta_sum(a1, a2):
    d = a1 - a2
    return np.sum(d**2)

def update_axes(changed_ax, axes):
    """Callback function to adapt all axes to the changed one."""

    # Changed axis
    new_xlim = changed_ax.get_xlim()
    new_ylim = changed_ax.get_ylim()

    for i, ax in enumerate(axes):

        # Prevent infinite recursion by checking whether axis is set to the correct value already
        if ax.get_xlim() != new_xlim:
            ax.set_xlim(new_xlim)

        if ax.get_ylim() != new_ylim:
            ax.set_ylim(new_ylim)

def plot_dual(wave_obj1, wave_obj2, offsets):
    # Plot data (assuming equal len)

    wave_len = wave_obj1.sample_cnt
    time = np.linspace(0, wave_len, wave_len)

    # Calculate delta

    # TODO Create subplots for wave1 and 2, left and right
    # wave1 L and wave2 L in one plot, wave1 R and wave2 R in the other
    fig, axes = plt.subplots(3)

    w1 = wave_obj1.data
    w2 = wave_obj2.data

    if not offsets[0]:
        offsets[0] = 0
    if not offsets[1]:
        offsets[1] = 0

    w2[:,0] = np.roll(w2[:,0], -offsets[0])
    w2[:,1] = np.roll(w2[:,1], -offsets[1])

    # Left channel
    axes[0].plot(time, w1[:,0], label='Wave 1 L', color='red')
    axes[0].plot(time, w2[:,0], label='Wave 2 L', color='blue')

    # Right channel
    axes[1].plot(time, w1[:,1], label='Wave 1 R', color='red')
    axes[1].plot(time, w2[:,1], label='Wave 2 R', color='blue')

    d = np.zeros((len(w1[:,0]),2))
    #dl = w1[:,0] - w2[:,0]
    d[:,0] = w1[:,0] - w2[:,0]
    d[:,1] = w1[:,1] - w2[:,1]
    #dr = w1[:,1] - w2[:,1]
    axes[2].plot(time, d[:,0], label='Delta L', color='green')
    axes[2].plot(time, d[:,1], label='Delta R', color='violet')

#    for ax in axes:
#        ax.callbacks.connect('xlim_changed', lambda event_ax: update_axes(event_ax, axes))
#        ax.callbacks.connect('ylim_changed', lambda event_ax: update_axes(event_ax, axes))

#    plt.suptitle(title)

#    plt.plot(time, wave2, label='Wave 2', color='blue')
    plt.show()

def calc_mismatches(wave1, wave2):

    # Calculate delta
    d = wave1-wave2

    mismatches = []

    # Find first non-zero sample
    for i in range(len(d)):
        if d[i] != 0:
            # Save indices of non-matching samples
            mismatches.append(i)
    
    bins = evaluate_diff(mismatches, len(d))

    if len(mismatches) > 0:
        fp = mismatches[0]
    return mismatches

# Compare two waveforms
# Return value:
#   None: Waveforms don't match at all
#   0:      Waveforms match perfectly
#   != 0:   Waveforms match with an offset
def compare_waveforms(w1, w2):
    if len(w1) != len(w2):
        # no match (length mismatch)
        return 0, False
    if delta_sum(w1, w2) == 0:
        # match without offset
        return 0, True

    # Get the first peak above a certain threshold on both waves
    height = 2048
    p1 = find_peaks(w1, height)
    p2 = find_peaks(w2, height)
    o = p2[0][0] - p1[0][0]

    # Shift waveforms
    w2_s = np.roll(w2, -o)
    if delta_sum(w1, w2_s) == 0:
        # match with offset
        return o, True, _
    else:
        # no match
        mism = calc_mismatches(w1, w2_s)
        return o, False, mism


def compare_files(fileA, fileB):
    w1 = wave_obj(fileA)
    w1.dump_short()
    w2 = wave_obj(fileB)
    w2.dump_short()

    offsets = [0, 0]
    match = [False, False]
    mismatches = [0,0]
    offsets[0], match[0], mismatches[0] = compare_waveforms(w1.data[:,0], w2.data[:,0])
    offsets[1], match[1], mismatches[1] = compare_waveforms(w1.data[:,1], w2.data[:,1])
    sample_cnt = w1.sample_cnt

    mismatches_uni = list(set(mismatches[0]).union(mismatches[1]))
    if offsets[0] == 0 and offsets[1] == 0 and match[0] and match[1]:
        print('Perfect match')
    elif match[0] == False or match[1] == False:
        print('No match')
        abs_tot = [0,0,0,0]
        for i in mismatches_uni:
            # Align waveforms using offset indetified
            w2r_l = np.roll(w2.data[:,0], -offsets[0])
            w2r_r = np.roll(w2.data[:,1], -offsets[1])
            abs_tot[0] += abs(w1.data[i,0])
            abs_tot[1] += abs(w2r_l[i])
            abs_tot[2] += abs(w1.data[i,1])
            abs_tot[3] += abs(w2r_r[i])
            # Print sample number, left channel of wave 1 and 2, right channel of wave 1 and 2
            print('[{}]: {:2} {:2} {:2} {:2}'.format(i, w1.data[i,0], w2r_l[i], w1.data[i,1], w2r_r[i]))
        print('Abs.tot:   {:2} {:2} {:2} {:2}'.format(abs_tot[0], abs_tot[1], abs_tot[2], abs_tot[3]))
        fp = np.array([mismatches[0][0], mismatches[1][0]])
        fp_perc = 100*fp[:]/sample_cnt
        print('{}/{} of {} non-matching samples. First one at: {} ({:.6f}%) and {} ({:.6f}%)'.format(len(mismatches[0]), len(mismatches[1]), sample_cnt,            fp[0], fp_perc[0], fp[1], fp_perc[1]))
    else:
       print('Match with offsets: {} / {}'.format(offsets[0], offsets[1]))

def get_files_from_path(path):
    # Collect files recursively
    filelist = []
    for root, _, files in os.walk(path):
        for filename in fnmatch.filter(files, "*.wav"):
            filelist.append(os.path.join(root, filename))
    return sorted(filelist)

def compare_folders(pathA, pathB):
    filesA = get_files_from_path(pathA)
    filesB = get_files_from_path(pathB)
    if len(filesA) != len(filesB):
        print('Number of files do not match')
        return
    for i in range(len(filesA)):
        print(filesA[i], filesB[i])
    for i in range(len(filesA)):
        compare_files(filesA[i], filesB[i])

#plot_dual(w1, w2, offsets)

def print_usage_and_die():
    print('Usage fileA|pathA fileB|pathB')
    print('Note: either provide two files or two paths')
    sys.exit(0)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('missing input file(s)/path(s)')
        print_usage_and_die()
    else:
        pathA = sys.argv[1]
        pathB = sys.argv[2]
        if os.path.isdir(pathA) and os.path.isdir(pathB):
            compare_folders(pathA, pathB)
        elif os.path.isfile(pathA) and os.path.isfile(pathB):
            compare_files(pathA, pathB)
        else:
            print('Note: either provide two files or two paths')
            print_usage_and_die()


