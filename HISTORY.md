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
* Expanding what counts as punctuation tokens.

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

v1.3, 18 April 2017
-------------------
* Added the `-r` / `--chars` option, which causes the tokens used to be characters, rather than words.
  * Still playing around with making this work, but it's basically solid.

v2.0, 20 April 2017
-------------------
* The parser has been rewritten to have an object-oriented interface when it's used as a library.
  * Passing around multiple variables for different aspects of the data was getting really unwieldy.
  * This makes everything a lot more conceptually simple, too: some ugly code has been eliminated.
  * This opens up more conceptually simple optoins for similar parsers with subclassing with minimal fuss.
    * Spoiler: there's going to be a first-pass poetry generator in the not-too-distant future.
* All command-line options are now working except for `-p`/`--pause`.
  * When that's working, the initial v2 will be merged into the master branch.
* This changes the interface to the unit.
  * Everything that depends on the old API will have to be adapted to the new protocol.
  * The amount of work required to keep the API consistent makes it not worthwhile.
    * Especially because, to the best of my knowledge, no one other than me is using this module.
* Still, at this point, it's mature enough to be tested with AutoLovecraft. Which I'm about to do.