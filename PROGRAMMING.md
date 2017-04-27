Programming the Markov Sentence Generator
=========================================

This document describes how to use Patrick Mooney's Markov chain-based sentence generator from Python 3.X code. Python 2.X is not supported. (Python 3.X has now been out for more than half of all the time since Python's first public release.) If what you're looking for is instructions for using the Markov chain-based sentence generator from your terminal rather than from Python code, you're reading the wrong document: you should look at the <a rel="me author" href="https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/README.md">README</a> file instead.

Overview
--------

`sentence_generator.py` is a Python module that exposes a `TextGenerator()` object. In order to generate text with it, you need to ...

1. Import the module, e.g. with `import sentence_generator as sg`
2. Instantiate a `TextGenerator` object, e.g. with `genny = sg.TextGenerator()`
  * If it's convenient for you, you can pass a name to the generator's creation procedure by doing something like `genny = sg.TextGenerator(name="MyTextGenerator")`; this does nothing except cause the name to be printed if the generator itself is printed
3. Train the object on a sample text (or multiple texts), which it will model and then use as the basis for creating text, e.g. with `genny.train(['/path/to/file.txt'])`
  * Note that you have to pass a list of files, even if that list only has one pathname.
4. Use the generator to produce some new text, e.g. with `genny.print_text(sentences_desired=8)`
  * There are other ways to generate text than just printing it to the terminal; read on for more details.
  
You can (of course!) use `help(sg)` or `dir(sg)` to explore the built-in documentation for the module.