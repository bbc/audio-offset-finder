# offset-finder
#
# Copyright (c) 2014 British Broadcasting Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from subprocess import Popen
from scipy.io import wavfile
from scikits.talkbox.features.mfcc import mfcc
import os, tempfile, warnings
import numpy as np

def find_offset(file1, file2, fs=8000, trim=60*15, correl_nframes=1000):
    tmp1 = convert_and_trim(file1, fs, trim)
    tmp2 = convert_and_trim(file2, fs, trim)
    # Removing warnings because of 18 bits block size
    # outputted by ffmpeg
    # https://trac.ffmpeg.org/ticket/1843
    warnings.simplefilter("ignore", wavfile.WavFileWarning)
    a1 = wavfile.read(tmp1, mmap=True)[1] / (2.0 ** 15)
    a2 = wavfile.read(tmp2, mmap=True)[1] / (2.0 ** 15)
    # We truncate zeroes off the beginning of each signals
    # (only seems to happen in ffmpeg, not in sox)
    a1, a2 = truncate(a1, a2)
    mfcc1 = mfcc(a1, nwin=256, nfft=512, fs=fs, nceps=13)[0]
    mfcc2 = mfcc(a2, nwin=256, nfft=512, fs=fs, nceps=13)[0]
    mfcc1 = std_mfcc(mfcc1)
    mfcc2 = std_mfcc(mfcc2)
    c = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    max_k_index = np.argmax(c)
    offset = max_k_index * 160.0 / float(fs) # * over / sample rate
    os.remove(tmp1)
    os.remove(tmp2)
    return offset

def truncate(signal1, signal2):
    non_zeros1 = np.where(signal1 > 0)[0]
    non_zeros2 = np.where(signal2 > 0)[0]
    if (len(non_zeros1) == 0 and len(non_zeros2) == 0):
        return (signal1, signal2)
    elif len(non_zeros1) == 0:
        trunc = non_zeros2[0] 
    elif len(non_zeros2) == 0:
        trunc = non_zeros1[0]
    else:
        first_non_zero1 = non_zeros1[0]
        first_non_zero2 = non_zeros2[0]
        trunc = max(first_non_zero1, first_non_zero2)
    return (signal1[trunc:], signal2[trunc:])

def cross_correlation(mfcc1, mfcc2, nframes):
    n1, mdim1 = mfcc1.shape
    n2, mdim2 = mfcc2.shape
    n = n1 - nframes + 1
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
    if not psox.returncode == 0:
        raise Exception("FFMpeg failed")
    return tmp_name
