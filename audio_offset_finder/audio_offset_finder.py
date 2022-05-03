# audio-offset-finder
#
# Copyright (c) 2014-22 British Broadcasting Corporation
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

from subprocess import Popen, PIPE
from scipy.io import wavfile
import librosa
import os
import tempfile
import warnings
import numpy as np


class InsufficientAudioException(Exception):
    pass


def mfcc(audio, win_length=256, nfft=512, fs=16000, hop_length=128, numcep=13):
    return [np.transpose(librosa.feature.mfcc(
        y=audio,
        sr=fs,
        n_fft=nfft,
        win_length=win_length,
        hop_length=hop_length,
        n_mfcc=numcep))]


def find_offset(file1, file2, fs=8000, trim=60*15, hop_length=128, win_length=256, nfft=512, plot=False):
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
    a1 = ensure_non_zero(a1)
    a2 = ensure_non_zero(a2)

    mfcc1 = mfcc(a1, win_length=win_length, nfft=nfft, fs=fs, hop_length=hop_length, numcep=26)[0]
    mfcc2 = mfcc(a2, win_length=win_length, nfft=nfft, fs=fs, hop_length=hop_length, numcep=26)[0]
    mfcc1 = std_mfcc(mfcc1)
    mfcc2 = std_mfcc(mfcc2)

    # Derive correl_nframes from the length of audio supplied, to avoid buffer overruns
    correl_nframes = min(int(len(mfcc1)/3), len(mfcc2), 2000)
    if correl_nframes < 10:
        raise InsufficientAudioException(
            "Not enough audio to analyse - try longer clips, less trimming, or higher resolution.")

    c = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    max_k_index = np.argmax(c)
    offset = (max_k_index) * hop_length / fs

    score = (c[max_k_index] - np.mean(c)) / np.std(c)  # standard score of peak
    os.remove(tmp1)
    os.remove(tmp2)
    return {"offset": offset, "score": score, "correlation": c}


def ensure_non_zero(signal):
    # We add a little bit of static to avoid
    # 'divide by zero encountered in log'
    # during MFCC computation
    signal += np.random.random(len(signal)) * 10**-10
    return signal


def cross_correlation(mfcc1, mfcc2, nframes):
    n1, mdim1 = mfcc1.shape
    n2, mdim2 = mfcc2.shape
    n = n1 - nframes + 1
    c = np.zeros(n)
    for k in range(n):
        cc = np.sum(np.multiply(mfcc1[k:k+nframes], mfcc2[:nframes]), axis=0)
        c[k] = np.linalg.norm(cc)
    return c


def std_mfcc(mfcc):
    return (mfcc - np.mean(mfcc, axis=0)) / np.std(mfcc, axis=0)


def convert_and_trim(afile, fs, trim):
    tmp = tempfile.NamedTemporaryFile(mode='r+b', prefix='offset_', suffix='.wav')
    tmp_name = tmp.name
    tmp.close()
    psox = Popen([
        'ffmpeg', '-loglevel', 'panic', '-i', afile,
        '-ac', '1', '-ar', str(fs), '-ss', '0', '-t', str(trim),
        '-acodec', 'pcm_s16le', tmp_name
    ], stderr=PIPE)
    psox.communicate()
    if not psox.returncode == 0:
        raise Exception("FFMpeg failed")
    return tmp_name
