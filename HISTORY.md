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

v1.1, 27 January 2016
---------------------
* Minor tweaks have happened here and there; I keep forgetting to update this HISTORY.md document.
* Added encoding declaration.

v1.1, 29 January 2016
----------------------
* Expanding what counds as punctuation tokens.

v1.1, 2 February 2016
---------------------
Still tweaking punctuation settings.

v1.1, 3 February 2016
----------------------
Pulled regex patterns to the front of the file, as constants. (Well, Python doesn't really have constants. Still.) Still tweaking the "what counts as a word?" question.


(missing notes, partially told in commit history)

v1.2, 24 January 2017
---------------------
Coming back to quick documentation of changes here.

`gen_text()` now uses text_handling.multi_replace() to do its substitutions
  * this means that they're now regex-based and that they keep getting applied until nothing produces a change.

25 March 2017
-------------
* Added the single-char ellipsis to the list of punctuations that count as tokens. Should have done that a while ago.
* Added several dash-related replacements to the final substitution list. 