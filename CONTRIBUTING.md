# Contributing

If you want to add functionality to this project, we welcome sugestions in the form of pull requests.

The base repository at https://github.com/bbc/audio-offset-finder is intended to be a simple, general purpose tool that can be used unaltered in many situations, and easily adapted to new use cases.
There are many forks of this tool targetting specific use cases, and this is a good thing.
Pull requests will be accepted if they add general-purpose functionality that is likely to significantly improve the usefulness of the tool for the majority of users, or if they fix bugs or otherwise improve the project.

Requested process:
 * This project uses feature branches - please create a Github fork of the project and do all of your changes within it, based on the master branch of this repository.
 * Make sure all your commits are as 'atomic' as possible (this way specific changes can be removed or cherry-picked more easily), and describe them thoughtfully in the commit messages.
 * Do not make pull requests monolithic in nature as this makes reviewing them difficult and chances are your pull request will be declined (depending on complexity).
 * If the word 'and' appears in the title of your pull request, it should probably be two requests.
 * A detailed pull request message that explains the purpose of the changes and answers any obvious questions about them is very helpful.
 * Wherever possible, submit tests for your patch/new feature so it can be tested easily.
 * Run pytest, and reformat your code with black (https://github.com/psf/black)<sup>†</sup> to ensure that the pull request will pass automated CI checks.

<sup>†</sup>Please make sure you install the version of black specified in setup.cfg, otherwise version incompatibilities may cause pull requests to be rejected.  One easy way to do this is to editably install the audio\_offset\_finder package locally using:
    pip install -e ".[dev]"


**Please raise any issues with this project as a GitHub issue.**
