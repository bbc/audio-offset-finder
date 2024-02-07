audio-offset-finder
===================

A simple tool and library for finding the offset of an audio file within another file.

The algorithm uses cross-correlation of standardised Mel-Frequency Cepstral Coefficients, so it should be relatively robust to noise (encoding, compression, etc).  The accuracy is typically to within about 0.01s.

The tool outputs the calculated offset in seconds, and a ["standard score"](https://en.wikipedia.org/wiki/Standard_score) indicating the prominence of the chosen correlation peak.  This can be used as a very rough estimate of the accuracy of the calculated offset - one with a score greater than ten is likely to be correct (at least for audio without similar repeated sections) within the accuracy of the tool; an offset with a score less than five is unlikely to be correct, and a manual check should be carried out.  Note that the value of the score depends on the length of the audio analysed.

The tool uses [FFmpeg](https://ffmpeg.org) for transcoding, so should work on all file formats supported by FFmpeg.  It is tested for compatibility with Python 3.8-3.12 on Linux, Windows and macOS.  Other Python versions and platforms may or may not work.

The aim of this open source project is to provide a simple tool and library that do one job well, and that can be the basis of customisation for more complex use cases.  The [forks of the base respository](https://github.com/bbc/audio-offset-finder/network/members) are worth exploring if you need a feature that is not included here.  The maintainers welcome pull requests with bug fixes, new features and other improvements that fit this philosophy - please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

Installation
------------

To install from source once downloaded [from GitHub](https://github.com/bbc/audio-offset-finder/):

    $ pip install .

Or, to install the latest package from PyPi.org:

    $ pip install audio-offset-finder

You will need to [install FFmpeg](https://ffmpeg.org/download.html) to use the command-line tool, or to use the file-related functions in the library.

Troubleshooting
---------------

This project uses Python's `distutils` library as part of the package build process.  This has been [removed from the standard library in Python 3.12 onwards](https://docs.python.org/3/whatsnew/3.12.html).  If you get an error saying "ModuleNotFoundError: No module named 'pkg_resources'", try installing the `setuptools` library, which provides the missing function calls:

    $ pip install setuptools

Usage
-----

To use the command-line tool:

    $ audio-offset-finder --help
    $ audio-offset-finder --find-offset-of file1.wav --within file2.wav
    Offset: 12.26 (seconds)
    Standard score: 28.99

    $ audio-offset-finder --find-offset-of file2.wav --within file1.wav
    Offset: -12.26 (seconds)
    Standard score: 28.99

To provide additional information about the accuracy of the result in addition to the standard score, the `--show-plot` option shows a plot of the cross-correlation curve, and the `--save-plot` option saves one to a file.  The two options can be used separately, or together if you want to both view the plot and save a copy of it:

    $ audio-offset-finder --find-offset-of file2.wav --within file1.wav --show-plot --save-plot example.png

A single well-defined peak such as the one shown in the image below is a good indication that the offset is correct.

<div style="width: 400; align:center">
<img alt="A line graph showing a cross-correlation curve with a sharp prominent peak emerging from low-level noise.  A dotted vertical line is overlaid at the position of the peak, indicating the position of the calculated offset." src="https://github.com/bbc/audio-offset-finder/raw/master/example_plot.png" title="Example correlation plot" />
</div>

Library Usage
-------------

To use the Python library:

```python
from audio_offset_finder.audio_offset_finder import find_offset_between_files

results = find_offset_between_files(filepath1, filepath2, trim=30)

print("Offset: %s (seconds)" % str(results["time_offset"]))
print("Standard score: %s" % str(results["standard_score"]))
```
A `find_offset_between_buffers()` function is also provided if you want to find offsets between audio buffers that you already
have in memory.

Testing
-------

    $ pytest

Similar Projects
----------------

If this tool doesn't meet your needs, there are others that you may wish to consider.  For example:
* [AudAlign](https://github.com/benfmiller/audalign) is a Python package and command-line tool for processing and aligning audio files using a variety of techniques.  It may therefore offer additional options in circumstances where this tool fails.  
* [AudioAlign](https://github.com/protyposis/AudioAlign) is a .NET GUI for the [Aurio](https://github.com/protyposis/Aurio) library.  It aims to solve the problem of synchronising audio and video recordings from the same event (or with the same audio tracks).

The inclusion of a tool in this list does not constitute a recommendation regarding its use.  You should carry out your own checks regarding performance, security, legality, appropriateness etc.

Copyright
---------

(c) 2014-2023 British Broadcasting Corporation and contributors

Licensing terms and authorship
------------------------------

See the [COPYING](COPYING) and [AUTHORS](AUTHORS) files.

For details of how to contribute changes, see [CONTRIBUTING.md](CONTRIBUTING.md).

The audio file used in the tests was downloaded from
[Wikimedia Commons](http://en.wikipedia.org/wiki/File:Tim_Berners-Lee_-_Today_-_9_July_2008.flac),
and was originally extracted from the 9 July 2008
episode of the BBC [Today programme](https://www.bbc.co.uk/programmes/b00cddwc).
