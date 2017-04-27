Programming the Markov Sentence Generator
=========================================

This document describes how to use Patrick Mooney's Markov chain-based sentence generator from Python 3.X code. Python 2.X is not supported. (Python 3.X has now been out for longer than 2.X was out before 3.X was out.) If what you're looking for is instructions for using the Markov chain-based sentence generator from your terminal rather than from Python code, you're reading the wrong document: you should look at the <a rel="me author" href="https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/README.md">README</a> file instead.

Overview
--------

`sentence_generator.py` is a Python module that exposes a `TextGenerator()` object. In order to generate text with it, you need to ...

<ol>
<li>Import the module, e.g. with <code>import sentence_generator as sg</code></li>
<li>Instantiate a `TextGenerator` object, e.g. with <code>genny = sg.TextGenerator()</code>
  <ol>
    <li>If it's convenient for you, you can pass a name to the generator's creation procedure by doing something like <code>genny = sg.TextGenerator(name="MyTextGenerator")</code>; this does nothing except cause the name to be printed if the generator object itself is passed to a procedure that creates a print representation</li>
  </ol>
</li>
<li>Train the object on a sample text (or multiple texts), which it will model and then use as the basis for creating text, e.g. with <code>genny.train(['/path/to/file.txt'])</code>
  <ol>
    <li>Note that you have to pass a <em>list</em> of files, even if that list only has one pathname.</li>
  </ol>
</li>
<li>Use the generator to produce some new text, e.g. with <code>genny.print_text(sentences_desired=8)</code>
  <ol>
    <li>There are other ways to generate text than just printing it to the terminal; read on for more details.</li>
  </ol>
</li>
</ol>
  
You can (of course!) use `help(sg)` or `dir(sg)` to explore the built-in documentation for the module.
