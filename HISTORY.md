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
* Added some (not enough) logging, based on my own `patrick_logger` module.
* Wrapped it in a set of routines that allow it meaningfully parse command-line options.
* Refactored again so that it's also usable as a Python module.
* Added a more comprehensive usage message.
* Added ability to store (`-o`) and load (`-l`) chains instead of creating them from scratch; this may help when runnng multiple times over the same text(s).
* Added ability to add multiple texts with `-i` or `--input`.

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

`gen_text()` now uses `text_handling.multi_replace()` to do its substitutions
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
  * This opens up more conceptually simple options for similar parsers with subclassing with minimal fuss.
    * Spoiler: there's going to be a first-pass poetry generator in the not-too-distant future.
* All command-line options are now working except for `-p`/`--pause`.
  * When that's working, the initial v2 will be merged into the master branch.
  * Well, that, and documentation has to be updated, too.
* This changes the interface to the unit.
  * Everything that depends on the old API will have to be adapted to the new protocol.
  * The amount of work required to keep the API consistent makes it not worthwhile. It's easier to adapt other projects to the new calling interface
    * Especially because, to the best of my knowledge, no one other than me is using this module.
* Still, at this point, it's mature enough to be tested with AutoLovecraft. Which I'm about to do.

24 April 2017
-------------
* All of the automatic text blogs are using it now except for *Ulysses Redux*, which will require a little more effort to rework.
  * Well, *Ulysses Redux* is a bit more complicated a project, after all.
  * Several minor bugs have been fixed, both in the text generator and in some of the blogs using it.
* Some *Ulysses Redux* scripts have been rewritten, as of today:
  * `ch07.py` ("Aeolus") -- seems to be working
  * `ch10.py` ("Wandering Rocks` -- seems to be working
  * `ch15.py` ("Circe") -- seems to be working
  * `ch17.py` ("Eumaeus") -- seems to be working
  * `generic_chapter.py`, which had its own calling interface changed; the following files that depend on it have been verified still to work:
    * `ch14.py`
    * `ch16.py`
    * `ch18.py`
    * `ch01.py`
    * `ch02.py`
    * `ch03.py`
    * `ch04.py`
    * `ch05.py`
    * `ch06.py`
    * `ch08.py`
    * `ch09.py`
    * `ch11.py`
    * `ch12.py`
    * `ch13.py`
* Fixed the documentation. It should be more or less up to date now. I think.

26 April 2017
-------------
* Added a series of interfaces to the set of final text-massaging substitutions that are performed on generated text.
  * `TextGenerator.add_final_substitution()`
  * `TextGenerator.remove_final_substitution()`
  * `TextGenerator.get_final_substitutions()`
  * `TextGenerator.set_final_substitutions()`
* Wrote first quick draft of a document describing the programming API to the text generator. It needs updating.

v2.1, 5 May 2017
----------------
* Updated some of the documentation, including the internal documentation to the script itself, which still occasionally referred to `text_generator` as `sentence_generator`. Whoops.
* Generating strings from a `TextGenerator()` object (i.e., anything that winds up funneling to a call to the object's `__str__()` method) now takes the possibility of unnamed generators into account with a bit more elegance.
* As a convenience, it's now possible to pass just a path to a file to the `train()` method instead of passing a list with one item.

v2.2, 12 May 2017
-----------------
* Incorporating `poetry_generator.py`, which subclasses `TextGenerator` to create (a very simplistic) `PoemGenerator`.
  * There's still a **lot** of work needed here.
  * Still, it's a start.
  * Samples of output from the developing poetry generator and scripts that call it are available [here](https://libidomechanica.tumblr.com/).

v2.3, 6 May 2020
----------------
* Refactoring a bit, and setting up Cython builds of the generators.

v2.4, 5 Dec 2020
----------------
* Added a number of interfaces to allow for fine-tuning of training parameters. Most notably,
  * `TextGenerator.addItemToTempMapping()` is no longer a static method and requires an instance to call.
  * `TextGenerator._build_mapping()` now takes two new optional parameters:
    * `learn_starts` (default `True`): whether this particular text should contribute to the underlying `starts` list of tokens; and
    * `weight` (default: 1.0) indicates how much emphasis (relative to other texts that the generator is seeing during its training cycle) this particular text should be given. Must be a positive number.
    * These two parameters may be useful when doing non-basic training procedures.
  * `TextGenerator.addItemToTempMapping()` also takes a `weight` parameter to pass it downwards to `_build_mapping()`.
  * Several object-attribute names have been renamed for the sake of concision.
    * Some local variables, too.