Programming the Markov Sentence Generator
=========================================

This document describes how to use Patrick Mooney's Markov chain-based sentence generator from Python 3.X code. Python 2.X is not supported. (Python 3.X has now been out for longer than 2.X was out before 3.X was out.) If what you're looking for is instructions for using the Markov chain-based sentence generator from your terminal rather than from Python code, you're reading the wrong document: you should look at the <a rel="me author" href="https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/README.md">README</a> file instead.

Overview
--------

`text_generator.py` is a Python module that exposes a `TextGenerator()` object. In order to generate text with it, you need to ...

<ol>
<li>Import the module, e.g. with <code>import text_generator as sg</code>.</li>
<li>Instantiate a `TextGenerator` object, e.g. with <code>genny = tg.TextGenerator()</code>.
  <ol>
    <li>If it's convenient for you, you can pass a name to the generator's creation procedure by doing something like <code>genny = tg.TextGenerator(name="MyTextGenerator")</code>; this does nothing except cause the name to be printed if the generator object itself is passed to a procedure that creates a print representation.</li>
  </ol>
</li>
<li>Train the object on a sample text (or multiple texts), which it will model and then use as the basis for creating text, e.g. with <code>genny.train(['/path/to/file.txt', '/path/to/another/file.txt']).</code>
  <ol>
    <li>If you're just training the generator on a single file, you need not wrap the pathname in a list.</li>
    <li>If you prefer, you can instead pass this file or list of files as the <code>training_texts</code> parameter when creating the object, as so: <code>genny = tg.TextGenerator(name="AwesomeTextGenerator", training_texts=['/path/to/a/text'])</code>
    <li>You can pass other arguments that wind up going to the <code>train()</code> method to the init code for the object, e.g. by doing something like <code>genny = tg.TextGenerator(name="MyTextGenerator", training_texts='/path/to/file', markov_length=3)</code>.</li>
  </ol>
</li>
<li>Use the generator to produce some new text, e.g. with <code>genny.print_text(sentences_desired=8)</code>
  <ol>
    <li>There are other ways to generate text than just printing it to the terminal:
      <ul>
        <li><code>a_string = genny.gen_html_frag(sentences_desired=8, paragraph_break_probability=0)</code> will generate text wrapped with HTML <code>&lt;p<gt; ... &lt/p%gt;</code> tags (though it does not generate a complete, formally valid HTML document).</li>
        <li><code>a_string = genny.gen_text(sentences_desired=8, paragraph_break_probability=0.125)</code> will generate some text and store it in <code>a_string</code>.</li>
      </ul>
    </li>
  </ol>
</li>
</ol>
  
You can (of course!) use `help(sg)` or `dir(sg)` to explore the built-in documentation for the module.
