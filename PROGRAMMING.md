Programming the Markov Sentence Generator
=========================================

This document describes how to use Patrick Mooney's Markov chain-based sentence generator from Python 3.X code. Python 2.X is not supported. (Python 3.X is now more than half as old as Python itself.) If what you're looking for is instructions for using the Markov chain-based sentence generator from your terminal rather than from Python code, you're reading the wrong document: you should look at the <a rel="me author" href="https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/README.md">README</a> file instead.

Overview
--------

`text_generator.py` is a Python module that exposes a `TextGenerator()` object. In order to generate text with it, you need to ...

<ol>
<li>Import the module, e.g. with <code>import text_generator as tg</code>.</li>
<li>Instantiate a <code>TextGenerator</code> object, e.g. with <code>genny = tg.TextGenerator()</code>.
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
        <li><code>a_string = genny.gen_html_frag(sentences_desired=8, paragraph_break_probability=0)</code> will generate text wrapped with HTML <code>&lt;p&gt; ... &lt;/p&gt;</code> tags (though this option does not cause a complete, formally valid HTML document to be generated).</li>
        <li><code>a_string = genny.gen_text(sentences_desired=8, paragraph_break_probability=0.125)</code> will generate some text and store it in <code>a_string</code>.</li>
      </ul>
    </li>
  </ol>
</li>
</ol>

The `TextGenerator` object is intentionally designed to be easily controllable by overriding its methods. Here's a list of methods that might be useful to override:

<dl>
  <dt><code>TextGenerator.comparison_form()</code></dt>
  <dd>A function that normalizes tokens for comparison purposes. The default function makes no changes at all (i.e., tokens are compared with no preprocessing). But tokens could in theory be compared in any number of ways, including by normalizing capitalization; there's an included <code>fix_caps</code> token comparison function that was written by Harry R. Schwartz in his older version of the Markov-based text generator; I myself have never used it (and suspect it might not quite do what he thinks it does; see comments in the code for more details), but it's there if you want it.</dd>
  
  <dt><code>TextGenerator._printer()</code></dt>
  <dd>A function responsible for printing generated text directly to the console. Override this function to change the details of how text is printed. An overridden version of this function will need to take the same arguments as this function does (or at least consume them, e.g. by =using a <code>*pargs</code>/<code>**kwargs</code> argument-consuming syntax).</dd>
</dl>

For an example of a simple class that overrides `TextGenerator()` productively, take a look at <code><a rel="me muse" href="https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/poetry_generator.py">poetry_generator.py</a></code>.
  
You can (of course!) use `help(tg)` or `dir(tg)` to explore the built-in documentation for the module.


Using with Cython
-----------------

`text_generator.py` and `poetry_generator.py` get a big performance boost when compiled with <a rel="muse" href="http://cython.org">Cython</a>, and improving performance with Cython is a long-term goal of this project. My own projects tend to use Cython-compiled versions of the text generators to save time and memory, in any case.

Once Cython and a C compiler are set up, `setup_tg.py` and `setup_pg.py` can be used to compile faster versions of the modules as static, compiled libraries using, for instance,

    python3 setup_tg.py build_ext --inplace
