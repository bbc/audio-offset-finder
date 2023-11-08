# audio-offset-finder
#
# Copyright (c) 2014-23 British Broadcasting Corporation
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
import numpy as np
import os
import types
from audio_offset_finder.cli import main, reorder_correlations
from unittest.mock import patch
from io import StringIO
import tempfile


def test_reorder_correlations():
    input_array1 = np.array([0, 1, 2, 3])
    np.testing.assert_array_equal(reorder_correlations(input_array1), np.array([2, 3, 0, 1]))

    input_array2 = np.array([0, 1, 2, 3, 4])
    np.testing.assert_array_equal(reorder_correlations(input_array2), np.array([2, 3, 4, 0, 1]))


def test_tool():
    temp_dir = tempfile.TemporaryDirectory()
    plot_file_path = os.path.join(temp_dir.name, "zzz.png")
    args1 = (
        "--find-offset-of tests/audio/timbl_2.mp3 --within tests/audio/timbl_1.mp3 --resolution 160 " "--trim 35 --save-plot "
    ) + plot_file_path
    with patch("sys.stdout", new=StringIO()) as fakeStdout:
        main(args1.split())
        output = fakeStdout.getvalue().strip()
        assert output, "audio_offset_finder did not produce any output"
        assert "Offset: 12.26" in output
        assert "score: 28" in output  # Different FFmpeg versions can slightly alter this value, so don't be too strict
    assert os.path.isfile(plot_file_path), "audio_offset_finder did not create a plot file"
    temp_dir.cleanup()

    args2 = "--find-offset-of tests/audio/timbl_2.mp3"
    with pytest.raises(SystemExit) as error:
        main(args2.split())
        assert error.type == SystemExit
        assert error.value.code > 0, "missing 'within' file"

    args3 = "--within tests/audio/timbl_1.mp3"
    with pytest.raises(SystemExit) as error:
        main(args3.split())
        assert error.type == SystemExit
        assert error.value.code > 0, "missing 'offset-of' file"


def test_json():
    import json

    args = "--find-offset-of tests/audio/timbl_2.mp3 --within tests/audio/timbl_1.mp3 --resolution 160 " "--trim 35 --json"
    with patch("sys.stdout", new=StringIO()) as fakeStdout:
        main(args.split())
        output = fakeStdout.getvalue().strip()
        json_array = json.loads(output)
        assert len(json_array) == 2
        assert pytest.approx(json_array["time_offset"]) == 12.26
        assert pytest.approx(json_array["standard_score"], rel=1e-2) == 28.99
