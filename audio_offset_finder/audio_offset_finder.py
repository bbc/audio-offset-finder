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
    """Thrown when there isn't enough audio to process"""
    pass


def mfcc(audio, win_length=256, nfft=512, fs=16000, hop_length=128, numcep=13):
    """Wraps the librosa MFCC routine.  Somewhat present for historical reasons at this point."""
    return [np.transpose(librosa.feature.mfcc(
        y=audio,
        sr=fs,
        n_fft=nfft,
        win_length=win_length,
        hop_length=hop_length,
        n_mfcc=numcep))]


def find_offset_between_files(file1, file2, fs=8000, trim=60*15, hop_length=128, win_length=256, nfft=512):
    """Find the offset time offset between two audio files.

    This function takes in two file paths, and (assuming they are media files with a valid audio track)
    compares them using cross-correlation of Mel Frequency Cepstral Coefficients to try and calculate
    the time offset between them, assuming that they are two recordings of the same thing.

    Parameters
    ----------
    file1: string
        A path to the reference file, in any format that FFMPEG can read
    file2: string
        A path to the comparison file, in any format that FFMPEG can read
    fs: int
        The sampling rate that the audio should be resampled to prior to MFCC calculation, in Hz
    trim: int
        The length to which input files will be truncated before processing, in seconds
    hop_length: int
        The number of samples (at the resampled rate "fs") to skip between each calculated MFCC frame
    win_length: int
        The length of the window function used to avoid transients adding spurious high frequencies to the MFCCs
    nfft: int
        The number of samples to use in the FFTs used to generate the MFCCs

    Returns
    -------
    A dict containing the following:
    time_offset (float): the most likely offset of file2 compared to file1, in seconds.  A positive value indicates that
                         file2 starts after file1
    frame_offset (int): the offset of file2 compared to file1, measured in MFCC frames
    standard_score (float): the standard score of the highest correlation coefficient in the cross-correlation curve
    correlation (numpy int array): the 1D array of correlation coefficients calculated for the two input files
    time_scale: the scalar factor that is multiplied to frame offsets to convert them to time offsets
    earliest_frame_offset (int): the earliest offset searched for a correlation.  Always negative.
    latest_frame_offset (int): the latest offset searched for a correlation.  Always positive.

    Throws
    ------
    InsufficientAudioException if the audio supplied is too short to analyse.
    """
    tmp1 = convert_and_trim(file1, fs, trim)
    tmp2 = convert_and_trim(file2, fs, trim)
    # Removing warnings because of 18 bits block size
    # outputted by ffmpeg
    # https://trac.ffmpeg.org/ticket/1843
#    warnings.simplefilter("ignore", wavfile.WavFileWarning)
    a1 = wavfile.read(tmp1, mmap=True)[1] / (2.0 ** 15)
    a2 = wavfile.read(tmp2, mmap=True)[1] / (2.0 ** 15)
    offset_dict = find_offset_between_buffers(a1, a2, fs, hop_length, win_length, nfft)
    os.remove(tmp1)
    os.remove(tmp2)
    return offset_dict


def find_offset_between_buffers(buffer1, buffer2, fs, hop_length=128, win_length=256, nfft=512):
    """Find the offset time offset between two audio files.

    This function takes in two numpy arrays (assumed to be PCM audio) and compares them using cross-correlation of
    Mel Frequency Cepstral Coefficients to try and calculate the time offset between them, assuming that they are
    two recordings of the same thing.

    Parameters
    ----------
    buffer1: numpy array
        The first audio buffer to compare
    buffer2: numpy array
        The second audio buffer to compare
    fs: int
        The sampling rate of the two audio buffers, in Hz
    hop_length: int
        The number of samples to skip between each calculated MFCC frame
    win_length: int
        The length of the window function used to avoid transients adding spurious high frequencies to the MFCCs
    nfft: int
        The number of samples to use in the FFTs used to generate the MFCCs

    Returns
    -------
    A dict containing the following:
    time_offset (float): the most likely offset of buffer2 compared to buffer1, in seconds.  A positive value indicates that
                         buffer2 starts after buffer1
    frame_offset (int): the offset of buffer2 compared to buffer1, measured in MFCC frames
    standard_score (float): the standard score of the highest correlation coefficient in the cross-correlation curve
    correlation (numpy int array): the 1D array of correlation coefficients calculated for the two input buffers
    time_scale: the scalar factor that is multiplied to frame offsets to convert them to time offsets
    earliest_frame_offset (int): the earliest offset searched for a correlation.  Always negative.
    latest_frame_offset (int): the latest offset searched for a correlation.  Always positive.

    Throws
    ------
    InsufficientAudioException if the audio supplied is too short to analyse.
    """
    a1 = ensure_non_zero(buffer1)
    a2 = ensure_non_zero(buffer2)

    mfcc1 = mfcc(a1, win_length=win_length, nfft=nfft, fs=fs, hop_length=hop_length, numcep=26)[0]
    mfcc2 = mfcc(a2, win_length=win_length, nfft=nfft, fs=fs, hop_length=hop_length, numcep=26)[0]
    mfcc1 = std_mfcc(mfcc1)
    mfcc2 = std_mfcc(mfcc2)

    # Derive correl_nframes from the length of audio supplied, to avoid buffer overruns
    correl_nframes = min(int(len(mfcc1)/3), len(mfcc2), 2000)
    if correl_nframes < 10:
        raise InsufficientAudioException(
            "Not enough audio to analyse - try longer clips, less trimming, or higher resolution.")

    c, earliest_frame_offset, latest_frame_offset = cross_correlation(mfcc1, mfcc2, nframes=correl_nframes)
    max_k_index = np.argmax(c)
    max_k_frame_offset = max_k_index
    if max_k_index > len(c) / 2:
        max_k_frame_offset -= len(c)
    time_scale = hop_length / fs
    time_offset = (max_k_frame_offset) * time_scale

    score = (c[max_k_index] - np.mean(c)) / np.std(c)  # standard score of peak
    return {"time_offset": time_offset,
            "frame_offset": int(max_k_index),
            "standard_score": score,
            "correlation": c,
            "time_scale": time_scale,
            "earliest_frame_offset": int(earliest_frame_offset),
            "latest_frame_offset": int(latest_frame_offset)}


def ensure_non_zero(signal):
    """Add very low level white noise to a signal to prevent divide-by-zero errors during MFCC calculation.
    (May be redundant following the switch to librosa for MFCCs)"""
    signal += np.random.random(len(signal)) * 10**-10
    return signal


# returns an array in which the first half represents an offset of mfcc2 within mfcc2,
# and the second half (accessed by negative indices) vice-versa.
def cross_correlation(mfcc1, mfcc2, nframes):
    """Calculate the cross-correlation curve between two numpy arrays (assumed to be MFCCs).

    Parameters
    ----------
    mfcc1: numpy array
        The first array to correlate
    mfcc2: numpy array
        The second array to correlate
    nframes: int
        The number of frames to correlate between the two arrays

    Returns
    -------
    A numpy array containing the cross-correlation of the two arrays for each possible offset between them.
    The zeroth element contains the cross-correlation with no offset.
    The first half of the array (up to len(c)/2) contains offsets of mfcc2 within mfcc1.
    The second half of the array contains offsets of mfcc1 within mfcc2.
    This is done so that accessing the array with an index in the range -(len(c)/2) to (len(c)/2) will return
    an appropriate cross-correlation coefficient for that offset.
    """
    n1, mdim1 = mfcc1.shape
    n2, mdim2 = mfcc2.shape
    n_min = nframes - n1
    n_max = n1 - nframes + 1
    n = n_max - n_min
    c = np.zeros(n)
    for k in range(n_min, 0):
        cc = np.sum(np.multiply(mfcc1[:nframes], mfcc2[-k:nframes-k]), axis=0)
        c[k] = np.linalg.norm(cc)
    for k in range(n_max):
        cc = np.sum(np.multiply(mfcc1[k:k+nframes], mfcc2[:nframes]), axis=0)
        c[k] = np.linalg.norm(cc)
    return c, n_min, n_max


def std_mfcc(array):
    """Returns the standard score for each offset of a given numpy array"""
    return (array - np.mean(array, axis=0)) / np.std(array, axis=0)


def convert_and_trim(afile, fs, trim):
    """Converts the input media to a temporary 16-bit WAV file and trims it to length.

    Parameters
    ----------
    afile: string
        The input media file to process.  It must contain at least one audio track.
    fs: int
        The sample rate that the audio should be converted to during the conversion
    trim: float
        The length to which the output audio should be trimmed, in seconds.  (Audio beyond this point will be discarded.)

    Returns
    -------
    A string containing the path of the processed media file.  You should delete this file after use.
    """
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
