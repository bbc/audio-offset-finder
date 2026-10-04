# audio-offset-finder
#
# Copyright (c) 2014-24 British Broadcasting Corporation
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
from unittest.mock import patch
from audio_offset_finder.audio_offset_finder import find_offset_between_buffers
from audio_offset_finder import audio_offset_finder as finder


@pytest.mark.parametrize("failure_stage", ["conversion", "read", "analysis"])
def test_failed_analysis_removes_temporary_audio(tmp_path, monkeypatch, failure_stage):
    created = []
    error = RuntimeError("audio processing failed")

    def convert(*args):
        if failure_stage == "conversion" and created:
            raise error
        filename = tmp_path / (str(len(created)) + ".wav")
        filename.write_bytes(b"temporary audio")
        created.append(filename)
        return str(filename)

    def read(*args, **kwargs):
        if failure_stage == "read":
            raise error
        return 8000, np.zeros(32)

    def analyze(*args, **kwargs):
        raise error

    monkeypatch.setattr(finder, "convert_and_trim", convert)
    monkeypatch.setattr(finder.wavfile, "read", read)
    monkeypatch.setattr(finder, "find_offset_between_buffers", analyze)

    with pytest.raises(RuntimeError) as caught:
        find_offset_between_files("first.mp3", "second.mp3")
    assert caught.value is error
    assert created
    assert all(not filename.exists() for filename in created)


def test_failed_conversion_removes_partial_output(tmp_path, monkeypatch):
    monkeypatch.setattr(finder.tempfile, "tempdir", str(tmp_path))

    class FailedFFmpeg:
        returncode = 1

        def __init__(self, command, **kwargs):
            self.output = command[-1]

        def communicate(self):
            with open(self.output, "wb") as output:
                output.write(b"partial WAV")
            return None, "conversion failed"

    monkeypatch.setattr(finder, "Popen", FailedFFmpeg)
    with pytest.raises(Exception, match="FFMpeg failed:\\nconversion failed"):
        finder.convert_and_trim("bad.mp3", 8000, None)
    assert list(tmp_path.iterdir()) == []


def test_find_offset_at_earliest_boundary():
    rng = np.random.default_rng(0)
    first = rng.normal(size=(30, 26))
    second = np.concatenate((rng.normal(size=(10, 26)), first[:10]))
    with patch("audio_offset_finder.audio_offset_finder.mfcc", side_effect=[[first], [second]]):
        result = find_offset_between_buffers(np.zeros(1), np.zeros(1), fs=8000, hop_length=128)
    assert result["frame_offset"] == -10
    assert result["time_offset"] == pytest.approx(-0.16)


def path(test_file):
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "audio", test_file))


def test_find_offset_between_files():
    # timbl_1.mp3: Full file
    # timbl_2.mp3: File truncated at 12.254 seconds
    # timbl_3.mp3: File truncated at 12.223 seconds with white noise added to it
    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=35)
    assert results["time_offset"] == pytest.approx(12.26)
    assert results["standard_score"] == pytest.approx(28.99, rel=1e-2)

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_3.mp3"), hop_length=160, trim=35)
    assert results["time_offset"] == pytest.approx(12.24)
    assert results["standard_score"] == pytest.approx(23.49, rel=1e-2)

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_1.mp3"), hop_length=160, trim=35)
    assert results["time_offset"] == pytest.approx(0.0)
    assert results["standard_score"] == pytest.approx(33.79, rel=1e-2)

    results = find_offset_between_files(path("timbl_2.mp3"), path("timbl_2.mp3"), hop_length=160, trim=35)
    assert results["time_offset"] == pytest.approx(0.0)
    assert results["standard_score"] == pytest.approx(32.48, rel=1e-2)

    results = find_offset_between_files(path("timbl_2.mp3"), path("timbl_1.mp3"), hop_length=160, trim=35)
    assert results["time_offset"] == pytest.approx(-12.26)
    assert results["standard_score"] == pytest.approx(28.99, rel=1e-2)

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=1)
    assert results["standard_score"] == pytest.approx(2.60, rel=1e-2)  # No good results["offset"] found

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160)
    assert results["time_offset"] == pytest.approx(12.26)
    assert results["standard_score"] == pytest.approx(
        30.09, rel=1e-2
    )  # standard score increases with more audio in cross-correlation

    with pytest.raises(InsufficientAudioException):
        find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, trim=0.1)

    results = find_offset_between_files(path("timbl_1.mp3"), path("timbl_2.mp3"), hop_length=160, max_frames=100)
    print((results["time_offset"], results["standard_score"]))

    with pytest.raises(Exception) as exception:
        find_offset_between_files(path("dummy.mp3"), path("timbl_2.mp3"), hop_length=160, trim=0.1)
    assert exception.value.args[0].startswith("FFMpeg failed:\n")
    assert exception.value.args[0].endswith("No such file or directory")

    results = find_offset_between_files(path("r4.ogg"), path("r4_excerpt.ogg"), hop_length=128, trim=20 * 60)
    assert results["time_offset"] == pytest.approx(334.608)
    assert results["standard_score"] == pytest.approx(43.37, rel=1e-2)

    results = find_offset_between_files(path("r4.ogg"), path("r4_excerpt2.ogg"), hop_length=128, trim=20 * 60)
    assert results["time_offset"] == pytest.approx(726.4)
    assert results["standard_score"] == pytest.approx(58.66, rel=1e-2)


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
