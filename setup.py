#!/usr/bin/env python

from setuptools import setup

setup(
    name='offset-finder',
    version='0.0.4',
    description='Find offset of audio file within another audio file',
    author='Yves Raimond',
    author_email='yves.raimond@bbc.co.uk',
    packages=['.'],
    install_requires=[
        'scipy',
        'numpy',
        'scikits.talkbox', 
    ],
    scripts=['bin/offset-finder'],
)

