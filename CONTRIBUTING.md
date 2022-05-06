# Contributing

If you want to add functionality to this project, we welcome sugestions in the form of pull requests.

The base repository at https://github.com/bbc/audio-offset-finder is intended to be a simple, general purpose tool that can be used unaltered in many situations, and easily adapted to new use cases.
There are many forks of this tool targetting specific use cases, and this is a good thing.
Pull requests will be accepted if they add general-purpose functionality that is likely to significantly improve the usefulness of the tool for the majority of users.

Requested process:
 * Create a fork based on master and do all of your changes within it
 * Make sure commits are as 'atomic' as possible (this way specific changes can be removed or cherry-picked more easily), and describe them thoughtfully in the commit message
 * Do not make pull requests monolithic in nature as this makes reviewing difficult and chances are your pull request will be declined (depending on complexity)
 * If the word 'and' appears in the title of your pull request, it should probably be two requests
 * Provide a summary of the main changes and their purpose in the pull request message
 * Wherever possible, submit tests for your patch/new feature so it can be tested easily
 * Run pytest, and lint your code with flake8 using the settings in .github/workflows/python-package.yml, to ensure that the pull request will pass automated CI checks

**Please raise any issues with this project as a GitHub issue.**