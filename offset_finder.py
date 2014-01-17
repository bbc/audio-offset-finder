#!/usr/bin/python

from subprocess import Popen
from scipy.io import wavfile
from scikits.talkbox.features.mfcc import mfcc
import os, tempfile
import numpy as np

def find_offset(file1, file2, fs=8000, trim=60*15, correl_nframes=1000):
    tmp1 = convert_and_trim(file1, fs, trim)
    tmp2 = convert_and_trim(file2, fs, trim)
    a1 = wavfile.read(tmp1, mmap=True)[1] / (2.0 ** 15)
    a2 = wavfile.read(tmp2, mmap=True)[1] / (2.0 ** 15)
    os.remove(tmp1)
    os.remove(tmp2)
    mfcc1 = mfcc(a1, nwin=256, nfft=512, fs=fs, nceps=13)[0]
    mfcc2 = mfcc(a2, nwin=256, nfft=512, fs=fs, nceps=13)[0]
    c = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    max_k_index = np.argmax(c)
    offset = max_k_index * 160.0 / float(fs) # * over / sample rate
    return offset

def cross_correlation(mfcc1, mfcc2, nframes):
    mfcc1 = std_mfcc(mfcc1)
    mfcc2 = std_mfcc(mfcc2)
    n1, mdim1 = mfcc1.shape
    n2, mdim2 = mfcc2.shape
    n = min(n1, n2) - nframes
    c = np.zeros(n)
    for k in range(0, n):
        cc = np.sum(np.multiply(mfcc1[k:k+nframes], mfcc2[0:nframes]), axis=0)
        c[k] = np.linalg.norm(cc)
    return c

def std_mfcc(mfcc):
    return (mfcc - np.mean(mfcc, axis=0)) / (np.max(mfcc,axis=0) - np.min(mfcc,axis=0))

def convert_and_trim(afile, fs, trim):
    tmp = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_', suffix='.wav')
    tmp_name = tmp.name
    tmp.close()
    psox = Popen(['ffmpeg', '-loglevel', 'quiet', '-i', afile, '-ac', '1', '-ar', str(fs), '-ss', '0', '-t', str(trim), '-acodec', 'pcm_s16le', tmp_name])
    psox.wait()
    return tmp_name
