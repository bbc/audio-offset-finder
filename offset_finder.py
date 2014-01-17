#!/usr/bin/python

from subprocess import Popen
from scipy.io import wavfile
from scikits.talkbox.features.mfcc import mfcc
import tempfile
import numpy as np

def find_offset(file1, file2):
    tmp1 = convert_and_trim(file1)
    tmp2 = convert_and_trim(file2)
    a1 = wavfile.read(tmp1)[1] / (2.0 ** 15)
    a2 = wavfile.read(tmp2)[1] / (2.0 ** 15)
    mfcc1 = mfcc(a1, nwin=256, nfft=512, fs=16000, nceps=13)[0]
    mfcc2 = mfcc(a2, nwin=256, nfft=512, fs=16000, nceps=13)[0]
    c = cross_correlation(mfcc1, mfcc2)
    max_k_index = np.argmax(c)
    offset = max_k_index * 160.0 / 16000.0 # * over / sample rate
    return offset

def cross_correlation(mfcc1, mfcc2, nframes=1000):
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

def convert_and_trim(file1):
    tmp1 = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_', suffix='.wav')
    tmp1_name = tmp1.name
    tmp1.close()
    psox = Popen(['sox', file1, '-c', '1', '-r', '16000', '-b', '16', tmp1_name, 'trim', '0', str(60 * 15)])
    psox.wait()
    return tmp1_name
