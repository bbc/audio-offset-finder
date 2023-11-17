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

import pytest
from audio_offset_finder.audio_offset_finder import find_offset_between_files, std_mfcc, cross_correlation
from audio_offset_finder.audio_offset_finder import InsufficientAudioException
import numpy as np
import os


def path(test_file):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "audio", test_file))


def test_find_offset_between_files():
    # timbl_1.mp3: Full file
    # timbl_2.mp3: File truncated at 12.254 seconds
    # timbl_3.mp3: File truncated at 12.223 seconds with white noise added to it
    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=35)
    assert pytest.approx(results["time_offset"]) == 12.26
    assert pytest.approx(results["standard_score"], rel=1e-2) == 28.99

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_3.mp3"), hop_length=160, trim=35)
    assert pytest.approx(results["time_offset"]) == 12.24
    assert pytest.approx(results["standard_score"], rel=1e-2) == 23.49

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_1.mp3"), hop_length=160, trim=35)
    assert pytest.approx(results["time_offset"]) == 0.0
    assert pytest.approx(results["standard_score"], rel=1e-2) == 33.79

    results = find_offset_between_files(path("timbl_2.mp3"), path("timbl_2.mp3"), hop_length=160, trim=35)
    assert pytest.approx(results["time_offset"]) == 0.0
    assert pytest.approx(results["standard_score"], rel=1e-2) == 32.48

    results = find_offset_between_files(path("timbl_2.mp3"), path("timbl_1.mp3"), hop_length=160, trim=35)
    assert pytest.approx(results["time_offset"]) == -12.26
    assert pytest.approx(results["standard_score"], rel=1e-2) == 28.99

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=1)
    assert pytest.approx(results["standard_score"], rel=1e-2) == 2.60  # No good results["offset"] found

    with pytest.raises(InsufficientAudioException):
        find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=0.1)

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, max_frames=100)
    print((results["time_offset"], results["standard_score"]))

    with pytest.raises(Exception) as exception:
        find_offset_between_files(path("dummy.mp3"), path("timbl_2.mp3"), hop_length=160, trim=0.1)
    assert exception.value.args[0].startswith("FFMpeg failed:\n")
    assert exception.value.args[0].endswith("No such file or directory")


def test_std_mfcc():
    m = np.array([[2, 3, 4], [4, 5, 5]])
    s1 = np.std([2, 4])
    s2 = np.std([3, 5])
    s3 = np.std([4, 5])
    np.testing.assert_array_equal(std_mfcc(m), np.array([[-1.0 / s1, -1.0 / s2, -0.5 / s3], [1.0 / s1, 1.0 / s2, 0.5 / s3]]))


def test_cross_correlation():
    m1 = np.array([[-0.5, -0.4, -0.4], [0.5, 0.5, 0.4], [0.1, -0.1, 0.1]])
    m2 = np.array([[0.5, 0.5, 0.4], [0.1, -0.1, 0.1], [-0.6, 0.0, -0.3]])
    c, n_min, n_max = cross_correlation(m1, m2, 2)
    assert np.argmax(c) == 1
    assert n_min == -1
    assert n_max == 2

    c, n_min, n_max = cross_correlation(m2, m1, 2)
    offset = np.argmax(c)
    if offset > len(c) / 2:  # argmax doesn't know that the cross-correlation array is centred on 0
        offset -= len(c)
    assert offset == -1
    assert n_min == -1
    assert n_max == 2

    m2 = m1
    c, n_min, n_max = cross_correlation(m1, m2, 2)
    assert np.argmax(c) == 0
    assert n_min == -1
    assert n_max == 2
