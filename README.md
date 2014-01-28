audio-offset-finder
===================

A simple tool for finding the offset of an audio file within another
file. 

Uses cross-correlation of standardised Mel-Frequency Cepstral Coefficients,
so should be relatively robust to noise (encoding, compression, etc).

It uses ffmpeg for transcoding, so should work on all file formats
supported by ffmpeg.

Installation
------------

    $ pip install offset-finder

Usage
-----

    $ offset-finder --help
    $ offset-finder --find-offset-of file1.wav --within file2.wav
    Offset: 300 (seconds)

Testing
-------

    $ nosetests

Licensing terms and authorship
------------------------------

See 'COPYING' and 'AUTHORS' files.
