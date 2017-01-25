Markov Sentence Generator
=========================

v1.2, 24 January 2017
----------------------

This program generates (one or more sentences of) "natural-sounding" text using a Markov model and sample textual training input.  Given some sample text from which to build a model, the program generates new text by randomly traversing a Markov chain that models the sources on which it was trained.  Use it from the terminal by doing something like:

`$ ./sentence_generator.py [options] -i FILENAME [-i FILENAME ] | -l FILENAME`

Non-Linux users may need to drop the `./` at the beginning of that command line. It should, in theory, run fine on non-Linux operating systems, but I haven't tested this, myself. Feedback is welcome on this or other matters.

sentence_generator.py needs existing text to use as the basis for the text that it generates. You must either specify at least one plain-text file (with `-i` or `--input`) for this purpose, or else must use `-l` to specify a file containing compiled probability data, saved with `-o` on a previous run. If you're looking for something to play with, try passing in a book from Project Gutenberg with `-i` or `--input` and trying passing different (fairly small) integers to the `-m` parameter, e.g. `-m 2` or `-m 5`.

A quick reference list of options you can pass in:

<table>
<tr><th scope="column">short form</th><th scope="column">long form</th><th scope="column">effect</th></tr>
<tr><td><code>-h</code></td><td><code>--help</code></td><td>Display a long help message.</td></tr>
<tr><td><code>-v</code></td><td><code>--verbose</code></td><td>Increase how chatty the script is.</td></tr>
<tr><td><code>-q</code></td><td><code>--quiet</code></td><td>Decrease how chatty the script is.</td></tr>
<tr><td><code>-m NUM</code></td><td><code>--markov-length=<wbr />NUM</code></td><td>Length (in words) of the Markov chains used by the program.</td></tr>
<tr><td><code>-i FILENAME</code></td><td><code>--input=<wbr />FILENAME</code></td><td>Specify an input file to use as the basis of the generated text.</td></tr>
<tr><td><code>-l FILE</code></td><td><code>--load=FILE</code></td><td>Load generated probability data ("chains") from a previous run that have been saved with -o or --output.</td></tr>
<tr><td><code>-o FILE</code></td><td><code>--output=FILE</code></td><td>Specify a file into which the generated probability data (the "chains") should be saved.</td></tr>
<tr><td><code>-c NUM</code></td><td><code>--count=NUM</code></td><td>Specify how many sentences the script should generate.</td></tr>
<tr><td><code>-w NUM</code></td><td><code>--columns=NUM</code></td><td>Currently unimplemented.</td></tr>
<tr><td><code>-p NUM</code></td><td><code>--pause=NUM</code></td><td>Currently unimplemented.</td></tr>
<tr><td>&nbsp;</td><td><code>--html</code></td><td>Wrap paragraphs of text output by the program with &lt;p&gt; ... &lt;/p&gt;.</td></tr> 
</table>

You can use `./sentence_generator.py --help` to get more detailed usage information. 

Chain length defaults to 1 (which is fastest), but increasing this may generate more "realistic" text (depending on how you evaluate that and how lucky the algorithm gets), albeit slightly more slowly.  Depending on the text, increasing the chain length past 6 or 7 words probably won't do much good -- at that point you're usually plucking out whole sentences anyway, so using a Markov model is kind of redundant.

This script is Patrick Mooney's fork of [Harry R. Schwartz's Markov Sentence Generator](https://github.com/hrs/markov-sentence-generator), modified for my automated text blog *Ulysses Redux*. (I also use it on many of <a rel="me" href="http://patrickbrianmooney.nfshost.com/~patrick/projects/#text-gen">my other automated text projects</a>.) HRS did the hard work here; my changes reflect adaptations to the needs of that particular project (and an opportunity to learn a bit about Python and Markov chain-based text processing). It also seeks to be more generally useful as a command-line program, though how well I have succeeded at that goal is (of course) a matter of opinion. The command-line interface options are intended to be a superset of those used in Jamie Zawinski's <a rel="muse" href="https://www.jwz.org/dadadodo/">DadaDodo</a>, which is also a Markov-based text generator (though this program is not explicitly intended to be a drop-in replacement for DadaDodo and—notably—it cannot read compiled DadaDodo chains, nor produce chains DadaDodo can read). 

If you want to develop this script, you are welcome to do so: I am interested in good ideas and welcome collaboration; and this script, like Schwartz's implementation, is licensed under the GPL, either version 3 or (at your option) any later option. A copy of [version 3 of the GPL](http://www.gnu.org/licenses/gpl-3.0.en.html) is included as the file [LICENSE.md](https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/LICENSE.md); a listing of changes is included as the file [HISTORY.md](https://github.com/patrick-brian-mooney/markov-sentence-generator/blob/master/HISTORY.md).

