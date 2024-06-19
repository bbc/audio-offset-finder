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

If you are installing on macOS and use the third-party package manager [HomeBrew](https://brew.sh), then [you may wish to use `pipx`](https://docs.brew.sh/Homebrew-and-Python) instead of `pip`.

You will need to [install FFmpeg](https://ffmpeg.org/download.html) to use the command-line tool, or to use the file-related functions in the library.

Basic Usage
-----------

To use the command-line tool:

    $ audio-offset-finder --help
    $ audio-offset-finder --find-offset-of file1.wav --within file2.wav
    Offset: 12.26 (seconds)
    Standard score: 28.99

    $ audio-offset-finder --find-offset-of file2.wav --within file1.wav
    Offset: -12.26 (seconds)
    Standard score: 28.99

Command-Line Options
--------------------
The following command-line options can be provided to alter the behaviour of the tool:

| Option | Description |
| ------ | ----------- |
| -h, --help  |  Show a help message and exit |
| --find-offset-of audio file | Find the offset of this file... |
| --within audio file  |  ...within this file |
| --sr sample rate |  Target sample rate in Hz during downsampling (default: 8000) |
| --trim seconds  |  Only use the first n seconds of each audio file |
| --resolution samples  |  Resolution (maximum accuracy) of search in samples (default: 128) |
| --show-plot  |  Display a plot of the cross-correlation results |
| --save-plot filename |  Save a plot of the cross-correlation results to a file (in a format that matches the extension you provide - png, ps, pdf, svg) |
| --json  |  Output in JSON for further processing |

You can fine-tune the results for your application by tweaking the sample rate, trim and resolution parameters:
* The _sample rate_ option refers to a resampling operation that is carried out before the audio offset search is carried out.  It does not refer to the sample rate(s) of the audio files being compared.  Resampling at a higher sample rate retains higher audio frequencies, but increases the time required to search for an offset.  The default sample rate is 8000Hz, which is a good compromise for most audio.
* The audio search is carried out by comparing the two audio files at a given offset, then skipping forward by a certain number of samples and then comparing them again.  This is repeated for all valid positions of one file compared to another, and then the best match is chosen and presented to the user.  The size of the skip is the _resolution_ of the search.  At a sample rate of 8000Hz (the default, as described above), a resolution of 128 samples (also the default) corresponds to a skip size of 128 / 8000 = 0.016 seconds.  This sets a limit on the precision of the offsets calculated by the tool.  You can make the search more precise by decreasing the value of _resolution_, but at the cost of increasing the processing time.
* An optional _trim_ operation can be carried out before processing.  If you specify a value here, only the given number of seconds from the beginning of each file will be searched for an offset.  This will prevent the tool from finding offsets unless they are somewhat less than the trim size.  It will also prevent the tool from finding offsets unless the similarities between the two audio files are present in the trimmed parts of the files.  If in doubt ensure that you select a trim size at least twice as large as the maximum possible offset, or leave it unspecified (the default) to search the whole range of each file.

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
A number of automated unit tests are included (and run before any pull requests are accepted) to try and validate the basic functionality of the tool in different scenarios.  You can run them yourself by simply installing pytest and running it in this repository's root folder:

    $ pytest

Similar Projects
----------------

If this tool doesn't meet your needs, there are others that you may wish to consider.  For example:
* [AudAlign](https://github.com/benfmiller/audalign) is a Python package and command-line tool for processing and aligning audio files using a variety of techniques.  It may therefore offer additional options in circumstances where this tool fails.  
* [AudioAlign](https://github.com/protyposis/AudioAlign) is a .NET GUI for the [Aurio](https://github.com/protyposis/Aurio) library.  It aims to solve the problem of synchronising audio and video recordings from the same event (or with the same audio tracks).

The inclusion of a tool in this list does not constitute a recommendation regarding its use.  You should carry out your own checks regarding performance, security, legality, appropriateness etc.

Copyright
---------

(c) 2014-2024 British Broadcasting Corporation and contributors

Licensing terms and authorship
------------------------------

See the [COPYING](COPYING) and [AUTHORS](AUTHORS) files.

For details of how to contribute changes, see [CONTRIBUTING.md](CONTRIBUTING.md).

The audio files used in the tests were downloaded from
[Wikimedia Commons](https://commons.wikimedia.org/wiki/Main_Page):
* [A recording of Tim Berners-Lee](https://commons.wikimedia.org/wiki/File:Tim_Berners-Lee_-_Today_(ffmpeg_FLAC_in_OGG).oga), originally extracted from the 9 July 2008 episode of the BBC [Today programme](https://www.bbc.co.uk/programmes/b00cddwc).  This file is licensed under the [Creative Commons](https://en.wikipedia.org/wiki/en:Creative_Commons) [Attribution 3.0 Unported](https://creativecommons.org/licenses/by/3.0/deed.en) license
* [A spoken word version](https://commons.wikimedia.org/wiki/File:BBC_Radio_4.ogg) of [the Wikipedia article on BBC Radio 4](https://en.wikipedia.org/wiki/BBC_Radio_4), spoken and recorded by Wikimedia Commons user [Tom Morris](https://commons.wikimedia.org/wiki/User:Tom_Morris).  This file is licensed under the [Creative Commons](https://en.wikipedia.org/wiki/en:Creative_Commons) [Attribution-Share Alike 3.0 Unported](https://creativecommons.org/licenses/by-sa/3.0/deed.en) license, and hence the excerpts created for use in the tests are also covered by that license.
