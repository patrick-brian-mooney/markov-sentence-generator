#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Patrick Mooney's Markov sentence generator, %s.

This script is available at
https://github.com/patrick-brian-mooney/markov-sentence-generator. See the
files README.md and LICENSE.md for more details.

USAGE:

  ./sentence_generator.py [options] -i FILENAME [-i FILENAME ] | -l FILENAME

sentence_generator.py needs existing text to use as the basis for the text that
it generates. You must either use -l to specify a file containing compiled
probability data, saved with -o on a previous run, or else must specify at
least one plain-text file (with -i or --input) for this purpose.

It can also be imported by a Python 3 script. A typical, fairly simple use
might be something like:

  #!/usr/bin/env python3
  from sentence_generator import *
  starts, the_mapping = _build_mapping(word_list('somefile.txt'), markov_length=2)
  print(gen_text(the_mapping, starts, markov_length=2, sentences_desired=24))

"""

__author__ = "Patrick Mooney, http://patrickbrianmooney.nfshost.com/~patrick/"
__version__ = "$v2.0 $"
__date__ = "$Date: 2017/04/19 16:16:00 $"
__copyright__ = "Copyright (c) 2015-17 Patrick Mooney"
__license__ = "GPL v3, or, at your option, any later version"

import re, random, sys, pickle, pprint, time, argparse, collections

import text_handling as th          # From  https://github.com/patrick-brian-mooney/personal-library
import patrick_logger               # From  https://github.com/patrick-brian-mooney/personal-library
from patrick_logger import log_it

# Set up some constants
patrick_logger.verbosity_level = 2  # Bump above zero to get more verbose messages about processing and to skip the
                                    # "are we running on a webserver?" check.

force_test = False

punct_with_space_after = r'.,\:!?;'
sentence_ending_punct = r'.!?'
punct_with_no_space_before = r'.,!?;—․-:/'
punct_with_no_space_after = r'—-/․'             # Note: that last character is U+2024, "one-dot leader".
word_punct = r"'’❲❳%°#․$"                       # Punctuation marks to be considered part of a word.
token_punct = r".,\:\-!?;—\/&…"                 # These punctuation marks also count as tokens.

final_substitutions = [                 # list of lists: each [search_regex, replace_regex]. Substitutions occur in order specified.
    ['--', '—'],
    ['\.\.\.', '…'],
    ['․', '.'],                         # replace one-dot leader with period
    ['\.\.', '.'],
    [" ' ", ''],
    ['――', '―'],                        # Two horizontal bars to one horizontal bar
    ['―-', '―'],                        # Horizontal bar-hyphen to single horizontal bar
    [':—', ': '],
    ["\n' ", '\n'],                     # newline--single quote--space
    ["<p>'", '<p>'],
    ["<p> ", '<p>'],                    # <p>-space to <p> (without space)
    ["<p></p>", ''],                    # <p></p> to nothing
    ['- ', '-'],                        # hyphen-space to hyphen
    ['—-', '—'],                        # em dash-hyphen to em dash
    ['——', '—'],                        # two em dashes to one em dash
    ['([0-9]),\s([0-9])', r'\1,\2'],    # Remove spaces after commas when commas are between numbers.
    ['([0-9]):\s([0-9])', r'\1:\2'],    # Remove spaces after colons when colons are between numbers.
]

default_args = {'chars': False,
                'columns': -1,
                'count': 1,
                'html': False,
                'input': [],
                'load': None,
                'markov_length': 1,
                'output': None,
                'pause': 0,
                'quiet': 0,
                'verbose': 0}


def print_usage():
    """Print a usage message to the terminal."""
    patrick_logger.log_it("INFO: print_usage() was called", 2)
    print('\n\n')
    print(__doc__ % __version__.strip('$').strip())

def print_html_docs():
    print('Content-type: text/html\n\n')                                # ... print HTTP headers, then documentation.
    print("""<!doctype html><html>
<head><title>Patrick Mooney's Markov chain–based text generator</title>
<link rel="profile" href="http://gmpg.org/xfn/11" /></head>
<body>
<h1>Patrick Mooney's Markov chain–based text generator</h1>
<p>Code is available <a rel="muse" href="https://github.com/patrick-brian-mooney/markov-sentence-generator">here</a>.</p>
<pre>%s</pre>
</body>
</html>"""% __doc__)
    sys.exit(0)


def process_acronyms(text):
    """Takes TEXT and looks through it for acronyms. If it finds any, it takes each
    and converts their periods to one-dot leaders to make the Markov parser treat
    the acronym as a single word.

    This function is NEVER called directly by any other routine in this file;
    it's a convenience function for code that uses this module.
    """
    remaining_to_process = text[:]
    ret = ""

    # First, search for and deal with sentence-ending acronyms. Doing this requires replacing their dots with a
    # one-dot leader, and then adding a sentence-ending period so the chain parser knows that there's sentence-ending
    # punctuation in the text.
    while remaining_to_process:
        match = re.search(r'([A-Z]\.){2,}\s[A-Z]', remaining_to_process, re.UNICODE) # Find acronym-whitespace-capital letter
        if match:
            ret += remaining_to_process[:match.start()]
            last_period = remaining_to_process[match.start() : match.end()].rfind('.')
            ret += remaining_to_process[match.start() : 1 + match.start() + last_period].replace('.', '․')
            ret += '.'
            ret += remaining_to_process[1 + match.start()+last_period : match.end()]
            remaining_to_process = remaining_to_process[match.end():]
        else:
            ret += remaining_to_process
            remaining_to_process = ""

    # Now, deal with any remaining unprocessed acronyms.
    remaining_to_process, ret = ret, ""
    while remaining_to_process:
        match = re.search(r'(?:(?<=\.|\s)[A-Z]\.)+', remaining_to_process, re.UNICODE)
        if match:
            ret += remaining_to_process[:match.start()]
            ret += remaining_to_process[match.start():match.end()].replace('.', '․')        # Replace periods with one-dot leaders
            remaining_to_process = remaining_to_process[match.end():]   # Lop off the part we've processed.
        else:
            ret += remaining_to_process
            remaining_to_process = ""
    return ret


def process_command_line():
    """Parse the command line; return a dictionary of selected options, accounting
    for defaults."""
    # import argparse
    # __version__ = "2"

    help_epilogue = """NOTES AND CAVEATS

Some options are incompatible with each other. Caveats for long options also
apply to the short versions of the same options.

  --input   ONLY understands PLAIN TEXT files. (Not HTML. Not markdown. Not MS
            Word. Not mailbox files. Not RTF. Just plain text.) Trying to feed
            it anything else will either fail or produce unpredictable results.

  --load    is quite convenient for multiple runs with the same data, but
            prevents changing the basic parameters for the model, because the
            encoded chains don't retain all of the data that was used to create
            them. If you're re-loading compiled data with this option, you cannot
            also use any of the following options:

            -m/--markov-length
            -i/--input
            -r/--chars (nor can you turn it off if the previously generated
                        chains were generated with it)

  --html    cannot be used with --columns/-w. (Rendered HTML ignores newlines
            anyway, so combining these two options will rarely or never make
            sense.)

            It also cannot be used with -p/--pause, because HTML output is not
            designed to be printed directly to the terminal, anyway.

  --output  does NOT specify an output file into which the generated text is
            saved. To do that, use shell redirection, e.g. by doing something
            like:

                ./sentence_generator -i somefile.txt > outputfile.txt

This program is licensed under the GPL v3 or, at your option, any later version. See the file LICENSE.md for details.

"""
    parser = argparse.ArgumentParser(description="This program generates random (but often intelligible) text based on a frequency\nanalysis of one or more existing texts. It is based on Harry R. Schwartz's\nMarkov sentence generator, but is intended to be more flexible for use in my own\nvarious text-generation projects.", epilog=help_epilogue, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-m', '--markov-length', type=int, default="1", metavar="N", help="""Length (in words; or, if -r is in effect, in characters) of the Markov chains used by the program. Longer chains generate text "more like the original text" in many ways, (often) including perceived grammatical correctness; but using longer chains also means that the sentences generated "are less random," take longer to generate and work with, and take more memory (and disk space) to store. Optimal values depend on the source text and its characteristics, but you might reasonably experiment with numbers from 1 to 4 to see what you get. Larger numbers will increasingly result in the script just coughing up whole sentences from the original source texts, which may or may not be what you want. The default Markov chain length, if not overridden with this parameter, is one.""")
    parser.add_argument('-i', '--input', metavar="FILE(s)", action="append", help="""Specify an input file to use as the basis of the generated text. You can specify this parameter more than once; all of the files specified will be treated as if they were one long file containing all of the text in all of the input files. If you are going to be regularly calling the script with the same input files, consider saving the probability data with -o, then loading that data with -l on subsequent runs; loading pre-compiled probability data with -l is much faster than re-generating it with -i.""")
    parser.add_argument('-o', '--output', metavar="FILE", help="""Specify a file into which the generated probability data (the "chains") should be saved. If you're going to be using the same data repeatedly, saving the data and then re-loading it with the -l option is faster than re-generating the data on every run by specifying the same input files with -i. However, if the Markov length is greater than 1, the generated chains are notably larger than the source files.""")
    parser.add_argument('-l', '--load', metavar="FILE", help="""Load generated probability data ("chains") from a previous run that have been saved with -o or --output.  Doing so is faster than re-generating the data, so if you're going to be using the same data a lot, you can save time by generating the data once.""")
    parser.add_argument('-c', '--count', metavar="N", type=int, default="1", help="""Specify how many sentences the script should generate. (If unspecified, the default number of sentences to generate is one.)""")
    parser.add_argument('-r', '--chars', action='store_true', help="""By default, the individual tokens in the chains generated by this program are whole words; chances are that this is what most people playing with a Markov chain-based text generator want most of the time anyway. However, if you specify -h or --chars, the tokens in the Markov chains are individual characters instead of words, and these individual characters are recombined to form random words (and, thereby, random sentences), instead of whole words being recombined to form random sentences. Doing this will certainly increase the degree to which the generated text is "gibberishy," especially if you don't also bump up the chain length with -m or --markov-length.""")
    parser.add_argument('-w', '--columns', metavar="N", type=int, default="-1", help="""Wrap the output to N columns. If N is -1 (or not specified), the sentence generator does its best to wrap to the width of the current terminal. If N is 0, no wrapping at all is performed, and words may be split between lines.""")
    parser.add_argument('-p', '--pause', metavar="N", type=int, default="0", help="""Pause NUM seconds after every paragraph is printed.""")
    parser.add_argument('--html', action='store_true', help="""Wrap paragraphs of text output by the program with HTML paragraph tags. It does NOT generate a complete, formally valid HTML document (which would involve generating a heading and title, among other things), but rather generates an HTML fragment that you can insert into another HTML document, as you wish.""")
    parser.add_argument('-v', '--verbose', action='count', default=0, help="""Increase the verbosity of the script, i.e. get more output. Can be specified multiple times to make the script more and more verbose. Current verbosity levels are subject to change in future versions of the script.""")
    parser.add_argument('-q', '--quiet', action='count', default=0, help="""Decrease the verbosity of the script. You can mix -v and -q, but really, what are you doing with your life?""")
    parser.add_argument('--version', action='version', version='sentence_generator.py %s' % __version__.strip('$').strip())
    return vars(parser.parse_args())

def to_hash_key(lst):
    """Tuples can be hashed; lists can't.  We need hashable values for dict keys.
    This looks like a hack (and it is, a little) but in practice it doesn't
    affect processing time too negatively."""
    return tuple(lst)

def apply_defaults(defaultargs, args):
    """Takes two dictionaries, ARGS and DEFAULTARGS, on the assumption that these are
    argument dictionaries for the **kwargs call syntax. Returns a new dictionary that
    consists of the elements of ARGS, plus those elements of DEFAULTARGS whose key
    names do not appear in ARGS. That is, this function merges the contents of
    DEFAULTARGS into ARGS, except for those keys that already exist in ARGS; these
    keys keep the value they initially had in ARGS. DEFAULTARGS is only used to
    supply missing keys.
    """
    ret = defaultargs.copy()
    ret.update(args)
    return ret

def fix_caps(word):
    """HRS initially said:
    "We want to be able to compare words independent of their capitalization."

    I disagree, though, so I'm commenting out this routine to see how that plays
    out.

    Schwartz further said:
    # Ex: "FOO" -> "foo"
    if word.isupper() and word != "I":
        word = word.lower()
        # Ex: "LaTeX" => "Latex"
    elif word[0].isupper():
        word = th.capitalize(word.lower())
        # Ex: "wOOt" -> "woot"
    else:
        word = word.lower()
    """
    return word


class MarkovChainTextModel(object):
    """Chains representing a model of a text."""
    def __init__(self):
        """Instantiate a new, empty set of chains."""
        self.the_starts = None              # List of tokens allowed at the beginning of a sentence.
        self.markov_length = 0          # Length of the chains.
        self.the_mapping = None         # Dictionary representing the Markov chains.
        self.character_tokens = False   # True if the chains are characters, False if they are words.

    def store_chains(self, filename):
        """Shove the relevant chain-based data into a dictionary, then pickle it and
        store it in the designated file.
        """
        chains_dictionary = { 'the_starts': self.the_starts,
                              'markov_length': self.markov_length,
                              'the_mapping': self.the_mapping,
                              'character_tokens': self.character_tokens }
        try:
            with open(filename, 'wb') as the_chains_file:
                the_pickler = pickle.Pickler(the_chains_file, protocol=-1)    # Use the most efficient protocol possible
                the_pickler.dump(chains_dictionary)
        except IOError as e:
            log_it("ERROR: Can't write chains to %s; the system said '%s'." % (filename, str(e)), 0)
        except pickle.PickleError as e:
            log_it("ERROR: Can't write chains to %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0)

    def read_chains(self, filename):
        """Read the pickled chain-based data from FILENAME."""
        default_chains = { 'character_tokens': False,       # We need only assign defaults for keys added in v2.0 and later.
                          }                                 # the_starts, the_mapping, and markov_length have been around since 1.0.
        try:
            with open(filename, 'rb') as the_chains_file:
                chains_dictionary = pickle.load(the_chains_file)
        except IOError as e:
            log_it("ERROR: Can't read chains from %s; the system said '%s'." % (filename, str(e)), 0)
        except pickle.PickleError as e:
            log_it("ERROR: Can't read chains from %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0)
        chains_dictionary = apply_defaults(defaultargs=default_chains, args=chains_dictionary)
        self.markov_length = chains_dictionary['markov_length']
        self.the_starts = chains_dictionary['the_starts']
        self.the_mapping = chains_dictionary['the_mapping']
        self.character_tokens = chains_dictionary['character_tokens']


class TextGenerator(object):
    """A general-purpose text generator. To use it, instantiate it, train it, and
    then have it generate text.
    """
    def __init__(self, name=None):
        """Create a new instance."""
        self.name = name                                # NAME is totally optional and entirely for your benefit.
        self.chains = MarkovChainTextModel()            # Markov chain-based representation of the text(s) used to train this generator.
        self.allow_single_character_sentences = False   # Is this model allowed to produce one-character sentences?

    def __str__(self):
        if self.is_trained():
            return '< class %s, named "%s", with Markov length %d >' % (self.__class__, self.name, self.chains.markov_length)
        else:
            return '< class %s, named "%s", UNTRAINED >' % (self.__class__, self.name)

    @staticmethod
    def addItemToTempMapping(history, word, the_temp_mapping):
        '''Self-explanatory -- adds "word" to the "the_temp_mapping" dict under "history".
        the_temp_mapping (and the_mapping) both match each word to a list of possible next
        words.

        Given history = ["the", "rain", "in"] and word = "Spain", we add "Spain" to
        the entries for ["the", "rain", "in"], ["rain", "in"], and ["in"].
        '''
        while len(history) > 0:
            first = to_hash_key(history)
            if first in the_temp_mapping:
                if word in the_temp_mapping[first]:
                    the_temp_mapping[first][word] += 1.0
                else:
                    the_temp_mapping[first][word] = 1.0
            else:
                the_temp_mapping[first] = {}
                the_temp_mapping[first][word] = 1.0
            history = history[1:]

    @staticmethod
    def next(prevList, the_mapping):
        """Returns the next word in the sentence (chosen randomly),
        given the previous ones.
        """
        sum = 0.0
        retval = ""
        index = random.random()
        # Shorten prevList until it's in the_mapping
        try:
            while to_hash_key(prevList) not in the_mapping:
                prevList.pop(0)
        except IndexError:  # If we somehow wind up with an empty list (shouldn't happen), then just end the sentence to
            # force us to start a new sentence.
            retval = "."
        # Get a random word from the_mapping, given prevList, if prevList isn't empty
        else:
            for k, v in the_mapping[to_hash_key(prevList)].items():
                sum += v
                if sum >= index and retval == "":
                    retval = k
                    break
        return retval

    def _build_mapping(self, token_list, markov_length, character_tokens=False):
        """Create the actual Markov chain-based training data for the model, based on an
        ordered list of tokens passed in.
        """
        the_temp_mapping = {}.copy()
        the_mapping = {}.copy()
        starts = [][:]
        starts.append(token_list[0])
        for i in range(1, len(token_list) - 1):
            if i <= markov_length:
                history = token_list[: i + 1]
            else:
                history = token_list[i - markov_length + 1 : i + 1]
            follow = token_list[i + 1]
            # if the last elt was a sentence-ending punctuation, add the next word to the start list
            if history[-1] in sentence_ending_punct and follow not in punct_with_space_after:
                starts.append(follow)
            self.addItemToTempMapping(history, follow, the_temp_mapping)
        # Now, normalize the values in the_temp_mapping and put them into the_mapping
        for first, followset in the_temp_mapping.items():
            total = sum(followset.values())
            the_mapping[first] = dict([(k, v / total) for k, v in followset.items()])   # Here's the normalizing step.
        self.chains.the_starts = starts
        self.chains.the_mapping = the_mapping
        self.chains.markov_length = markov_length
        self.chains.character_tokens = character_tokens

    @staticmethod
    def _token_list(the_string, character_tokens=False):
        """Converts a string into a set of tokens so that the text generator can
        process, and therefore be trained by, it.
        ."""
        if character_tokens:
            tokens = list(the_string)
        else:
            tokens = re.findall(r"[\w%s]+|[%s]" % (word_punct, token_punct), the_string)
        return [fix_caps(w) for w in tokens]

    def is_trained(self):
        """Detect whether this model is trained or not."""
        return (self.chains.the_starts and self.chains.the_mapping and self.chains.markov_length)

    def _train_from_text(self, the_text, markov_length=1, character_tokens=False):
        """Train the model by getting it to analyze a text passed in."""
        self._build_mapping(self._token_list(the_text, character_tokens=character_tokens),
                            markov_length=markov_length, character_tokens=character_tokens)

    def train(self, the_files, markov_length=1, character_tokens=False):
        """Train the model from a list of text files supplied as THE_FILES."""
        assert isinstance(the_files, list) or isinstance(the_files, tuple), "ERROR: you cannot pass an object of type %s to %s.train_from_files" % (type(the_files), self)
        assert len(the_files) > 0, "ERROR: empty file list passed to %s.train_from_files()" % self
        the_text = ""
        for which_file in the_files:
            with open(which_file) as the_file:
                the_text = the_text + '\n' + the_file.read()
        self._train_from_text(the_text=the_text, markov_length=markov_length, character_tokens=character_tokens)

    def _gen_sentence(self):
        """Build a sentence, starting with a random 'starting word.' Returns a string,
        which is the generated sentence.
        """
        assert self.is_trained(), "ERROR: the model %s needs to be trained before it can generate text" % self
        log_it("      _gen_sentence() called.", 4)
        log_it("        markov_length = %d." % self.chains.markov_length, 5)
        log_it("        the_mapping = %s." % self.chains.the_mapping, 5)
        log_it("        starts = %s." % self.chains.the_starts, 5)
        log_it("        allow_single_character_sentences = %s." % self.allow_single_character_sentences, 5)
        curr = random.choice(self.chains.the_starts)
        sent = curr
        prevList = [curr]
        # Keep adding words until we hit a period, exclamation point, or question mark
        while curr not in sentence_ending_punct:
            curr = self.next(prevList, self.chains.the_mapping)
            prevList.append(curr)
            # if the prevList has gotten too long, trim it
            while len(prevList) > self.chains.markov_length:
                prevList.pop(0)
            if not self.chains.character_tokens:            # Don't add spaces between tokens that are just single characters.
                if curr not in punct_with_no_space_before:
                    if (len(prevList) < 2 or prevList[-2] not in punct_with_no_space_after):
                        sent += " "                         # Add spaces between words (but not punctuation)
            sent += curr
        if not self.allow_single_character_sentences:
            if len(sent.strip().strip(sentence_ending_punct).strip()) == 1:
                if sent.strip().strip(sentence_ending_punct).strip().upper() != "I":
                    sent = self._gen_sentence()    # Retry, recursively.
        return th.capitalize(sent)

    def gen_text(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Actually generate some text."""
        log_it("gen_text() called.", 4)
        log_it("  Markov length is %d; requesting %d sentences." % (self.chains.markov_length, sentences_desired), 4)
        log_it("  Legitimate starts: %s" % self.chains.the_starts, 5)
        log_it("  Probability data: %s" % self.chains.the_mapping, 5)
        the_text = ""
        for which_sentence in range(0, sentences_desired):
            try:
                if the_text[-1] != "\n":        # If we're not starting a new paragraph ...
                    the_text = the_text + " "   #   ... add a space after the sentence-ending punctuation.
            except IndexError:                  # If this is the very beginning of our generated text ...
                pass                            #   ... well, we don't need to add a space to the beginning of the text, then.
            the_text = the_text + self._gen_sentence()
            if random.random() <= paragraph_break_probability:
                the_text = the_text.strip() + "\n\n"
        the_text = th.multi_replace(the_text, final_substitutions)
        return the_text

    def gen_html_frag(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Produce the same text that gen_text would, but wrapped in HTML <p></p> tags."""
        log_it("We're generating an HTML fragment.", 3)
        the_text = self.gen_text(sentences_desired, paragraph_break_probability)
        return '\n\n'.join(['<p>%s</p>' % p for p in the_text.split('\n\n')])


def main(**kwargs):
    """Handle the main program loop and generate some text.

    By default, this routine can simply be called as main(), with no arguments; this
    is what happens when the script is called from the command line. However, for
    testing purposes, it can also be called with keyword arguments in the same
    format that the command line would be parsed, i.e. with something like

        main(markov_length=2, input=['Song of Solomon.txt'], count=20, chars=True)

    """
    if (not sys.stdout.isatty()) and (patrick_logger.verbosity_level < 1):  # Assume we're running on a web server. ...
        generate_html_docs()

    if len(kwargs):     # If keyword arguments are passed in, trust them to be the options.
        opts = apply_defaults(defaultargs=default_args, args=kwargs)
    else:               # Otherwise, parse the command line.
        opts = process_command_line()

    # OK, check the parameters for inconsistencies.
    if not opts['load'] and not opts['input']:
        log_it('ERROR: You must specify input data using either -i/--input or -l/--load.')
        sys.exit(2)
    if opts['load']:
        if opts['input']:
            log_it('ERROR: You cannot both use --input/-i and --load/-l. Use one or the other.')
            sys.exit(2)
        if opts['markov_length'] > 1:
            log_it('ERROR: You cannot specify a Markov chain length if you load previously compiled chains with -l/--load.')
            sys.exit(2)
    if opts['html']:
        if opts['pause'] or opts['columns'] > 0:
            log_it('ERROR: Specifying --html is not compatible with using a --pause/-p value or specifying a column width.')
            sys.exit(2)

    # Now set up logging parameters
    log_it('INFO: Command-line options parsed; parameters are: %s' % pprint.pformat(opts))
    patrick_logger.verbosity_level = opts['verbose'] - opts['quiet']
    log_it('DEBUGGING: verbosity_level after parsing command line is %d.' % patrick_logger.verbosity_level, 2)

    # Now instantiate and train the model, and save the compiled chains, if that's what the user wants
    genny = TextGenerator()
    if opts['load']:
        genny.chains.read_chains(filename=opts['load'])
    else:
        genny.train(the_files=opts['input'], markov_length=opts['markov_length'], character_tokens=opts['chars'])
    if opts['output']:
        genny.chains.store_chains(filename=opts['output'])

    # And generate some text.
    if opts['html']:
        the_text = genny.gen_html_frag(sentences_desired=opts['count'])
    else:
        the_text = genny.gen_text(sentences_desired=opts['count'])

    if opts['columns'] == 0:        # Wrapping is totally disabled. Print exactly as generated.
        log_it("INFO: COLUMNS is zero; not wrapping text at all", 2)
        print(the_text)
        sys.exit(0)
    elif opts['columns'] == -1:     # Wrap to best guess for terminal width
        log_it("INFO: COLUMNS is -1; wrapping text to best-guess column width", 2)
        padding = 0
    else:                           # Wrap to specified width (unless current terminal width is odd, in which case we're off by 1)
        padding = max((th.terminal_width() - opts['columns']) // 2, 0)
        log_it("INFO: COLUMNS is %s; padding text with %s spaces on each side" % (opts['columns'], padding), 2)
        log_it("NOTE: terminal width is %s" % th.terminal_width())
    the_text = th.multi_replace(the_text, [['\n\n', '\n']])
    for the_paragraph in the_text.split('\n'):
        th.print_indented(the_paragraph, each_side=padding)
        print()


if __name__ == "__main__":
    if force_test:
        import glob
        main(count=20, load='/lovecraft/corpora/previous/Beyond the Wall of Sleep.2.pkl', html=True)
        pass
    else:
        main()
