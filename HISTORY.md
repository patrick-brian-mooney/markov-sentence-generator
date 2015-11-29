HISTORY
=======

v1, 13 October 2015
--------------------
* Initial fork from Harry R. Schwartz's [hrs/markov-sentence-generator](https://github.com/hrs/markov-sentence-generator).
* Samples were removed.
* This file was added.
* README.md was updated.

v1.1, 29 November 2015
----------------------
* Basic first release, this is alpha software, etc.
* Refactored Schwartz's program to avoid global variables.
* Added some (not enough) logging, based on the patrick_logger module.
* Wrapped it in a set of routines that allow it meaningfully parse command-line options.
* Refactored again so that it's also usable as a Python module.
* Added a more comprehensive usage message.
* Added ability to store (-o) and load (-l) chains instead of creating them from scratch; this may help when runnng multiple times over the same text(s).
* Added ability to add multiple texts with -i or --input.