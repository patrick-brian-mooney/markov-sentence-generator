#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Patrick Mooney's Markov sentence generator, %s.

This script is available at
https://github.com/patrick-brian-mooney/markov-sentence-generator. See the
files README.md and LICENSE.md for more details.

USAGE:

  ./text_generator.py [options] -i FILENAME [-i FILENAME ] | -l FILENAME

text_generator.py needs existing text to use as the basis for the text that
it generates. You must either use -l to specify a file containing compiled
probability data, saved with -o on a previous run, or else must specify at
least one plain-text file (with -i or --input) for this purpose.

For the full list of options, run

  ./text_generator.py --help

in a terminal.

It can also be imported by a Python 3 script. A typical, fairly simple use
might be something like:

  #!/usr/bin/env python3
  import text_generator as tg
  genny = tg.TextGenerator()
  genny.train('/path/to/a/text/file', markov_length=3)
  genny.print_text(sentences_desired=8)

"""

__author__ = "Patrick Mooney, http://patrickbrianmooney.nfshost.com/~patrick/"
__version__ = "$v2.0 $"
__date__ = "$Date: 2017/04/24 16:16:00 $"
__copyright__ = "Copyright (c) 2015-17 Patrick Mooney"
__license__ = "GPL v3, or, at your option, any later version"

import re, random, sys, pickle, pprint, time, argparse, collections

import text_handling as th          # From  https://github.com/patrick-brian-mooney/personal-library
import patrick_logger               # From  https://github.com/patrick-brian-mooney/personal-library
from patrick_logger import log_it

# Set up some constants
patrick_logger.verbosity_level = 1  # Bump above zero to get more verbose messages about processing and to skip the
                                    # "are we running on a webserver?" check.

force_test = False                  # IF we need to fake command-line arguments in an IDE for testing ...

punct_with_space_after = r'.,\:!?;'
sentence_ending_punct = r'.!?'
punct_with_no_space_before = r'.,!?;—․-:/'
punct_with_no_space_after = r'—-/․'             # Note: that last character is U+2024, "one-dot leader".
word_punct = r"'’❲❳%°#․$"                       # Punctuation marks to be considered part of a word.
token_punct = r".,:\-!?;—/&…⸻"                # These punctuation marks also count as tokens.


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
    it's a convenience function for code that uses this module. This may change
    in the future, if extensive testing shows there are very very few incorrect
    corrections made.
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
    for defaults.
    """

    help_epilogue = """OPTIONS

-m N, --markov-length N
    Length (in words; or, if -r is in effect, in characters) of the Markov
    chains used by the program. Longer chains generate text "more like the
    original text" in many ways, (often) including perceived grammatical
    correctness; but using longer chains also means that the sentences generated
    "are less random," take longer to generate and work with, and take more
    memory (and disk space) to store. Optimal values depend on the source text
    and its characteristics, but you might reasonably experiment with numbers
    from 1 to 4 to see what you get. Larger numbers will increasingly result in
    the script just coughing up whole sentences from the original source texts,
    which may or may not be what you want. The default Markov chain length, if
    not overridden with this parameter, is one.

-i FILE, --input FILE
    Specify an input file to use as the basis of the generated text. You can
    specify this parameter more than once; all of the files specified will be
    treated as if they were one long file containing all of the text in all of
    the input files.

-o FILE, --output FILE
    Specify a file into which the generated probability data (the "chains")
    should be saved. If you're going to be using the same data repeatedly,
    saving the data with -o and then re-loading it with the -l option is faster
    than re-generating the data on every run by specifying the same input files
    with -i. However, the generated chains saved with -o are notably larger than
    the source files.

-l FILE, --load FILE
    Load probability data ("chains") that was generated a previous run and
    saved with -o or --output.  Loading the data this way is faster than
    re-generating it, so if you're going to be using the same data a lot, you
    can save time by generating the data only once, then re-loading it this way
    on subsequent runs.

-c N, --count N
    Specify how many sentences the script should generate. (If unspecified, the
    default number of sentences to generate is one.)

-r, --chars
    By default, the individual tokens in the chains generated by this program
    are whole words; chances are that this is what most people using a Markov
    chain-based text generator want most of the time, anyway. However, if you
    specify -h or --chars, the tokens in the generated Markov chains will be
    individual characters, rather than words, and these individual characters
    will be recombined to form random words (and, thereby, random sentences),
    instead of whole words being recombined to form random sentences. Doing this
    will certainly increase the degree to which the generated text seems
    "gibberishy," especially if you don't also bump up the chain length with -m
    or --markov-length.

-w N, --columns N
    Wrap the output to N columns. If N is -1 (or not specified), the sentence
    generator does its best to wrap to the width of the current terminal. If N
    is 0, no wrapping at all is performed: words may be split between lines.

-p N, --pause N
    Pause approximately NUM seconds after each paragraph is printed. The actual
    pause may not be quite exactly NUM seconds, though the program tries to get
    this right to the greatest extent possible.

--html
    Wrap paragraphs of text output by the program with HTML paragraph tags. This
    does NOT generate a complete, formally valid HTML document (which would
    involve generating a heading and title, among other things), but rather
    generates an HTML fragment that you can insert into another HTML document,
    as you wish.

-v, --verbose
    Increase the verbosity of the script, i.e. get more output. Can be specified
    multiple times to make the script more and more verbose. Current verbosity
    levels are subject to change in future versions of the script.

-q, --quiet
    Decrease the verbosity of the script. You can mix -v and -q, but really,
    don't you have better things to do with your life?


NOTES AND CAVEATS

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
            intended to be printed directly to the terminal; and there's rarely
            any point in artificially slowing down content production intended
            for a web server, is there?

  --output  does NOT specify an output file into which the generated text is
            saved. To do that, use shell redirection, e.g. by doing something
            like:

                ./text_generator -i somefile.txt > outputfile.txt

This program is licensed under the GPL v3 or, at your option, any later version.
See the file LICENSE.md for details.

"""
    parser = argparse.ArgumentParser(description="This program generates random (but often intelligible) text based on a frequency\nanalysis of one or more existing texts. It is based on Harry R. Schwartz's\nMarkov sentence generator, but is intended to be more flexible for use in my own\nvarious text-generation projects.", epilog=help_epilogue, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-m', '--markov-length', type=int, default="1")
    parser.add_argument('-i', '--input', action="append")
    parser.add_argument('-o', '--output')
    parser.add_argument('-l', '--load')
    parser.add_argument('-c', '--count', type=int, default="1")
    parser.add_argument('-r', '--chars', action='store_true')
    parser.add_argument('-w', '--columns', type=int, default="-1")
    parser.add_argument('-p', '--pause', type=int, default="0")
    parser.add_argument('--html', action='store_true')
    parser.add_argument('-v', '--verbose', action='count', default=0)
    parser.add_argument('-q', '--quiet', action='count', default=0)
    parser.add_argument('--version', action='version', version='text_generator.py %s' % __version__.strip('$').strip())
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
    def __str__(self):
        if self.is_trained():
            if self.name:
                return '< class %s, named "%s", with Markov length %d >' % (self.__class__, self.name, self.chains.markov_length)
            else:
                return '< class %s (unnamed instance), with Markov length %d' % (self.__class__, self.chains.markov_length)
        else:
            if self.name:
                return '< class %s, named "%s", UNTRAINED >' % (self.__class__, self.name)
            else:
                return '< class %s (unnamed instance), UNTRAINED >' % self.__class__

    def __init__(self, name=None, training_texts=None):
        """Create a new instance. NAME is entirely optional, and is mentioned for 
        convenience (if it exists) any time a string representation is generated.
        If TRAINING_TEXTS is not None, it should be a *list* of one or more
        filenames on which the generator will be immediately trained. (You can
        instead call train() separately, if you wish.)
        """
        self.name = name                                # NAME is totally optional and entirely for your benefit.
        self.chains = MarkovChainTextModel()            # Markov chain-based representation of the text(s) used to train this generator.
        self.allow_single_character_sentences = False   # Is this model allowed to produce one-character sentences?

        # This next is the default list of substitutions that happen after text is produced.
        # List of lists. each sublist:[search_regex, replace_regex]. Subs performed in order specified.
        self.final_substitutions = [
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
            ['…—', '… —'],                      # put space in between ellipsis-em dash, if they occur together.
        ]
        if training_texts:
            self.train(training_texts)


    def add_final_substitution(self, substitution, position=-1):
        """Add another substitution to the list of substitutions performed after text is
        generated. Since the final substitutions are performed in the order they're
        listed, position matters; the POSITION parameter indicates what position in the
        list the new substitution will appear. If POSITION is -1 (the default), the new
        substitution appears at the end of the list.
        """
        assert isinstance(substitution, (list, tuple)), "ERROR: the substitution you pass in must be a list or tuple."
        assert len(substitution) == 2, "ERROR: the substitution you pass in must be two items long."
        if position == -1: position = len(self.final_substitutions)
        self.final_substitutions.insert(position, substitution)

    def remove_final_substitution(self, substitution):
        """Remove SUBSTITUTION from the list of final substitutions performed after text
        is generated. You must pass in *exactly* the substitution you want to remove.
        If you try to remove something that's not there, this routine will let the error
        raised by the list (which is always[?] ValueError) propagate -- trap it if you
        need to.
        """
        assert isinstance(substitution, (list, tuple)), "ERROR: the substitution you pass in must be a list or tuple."
        assert len(substitution) == 2, "ERROR: the substitution you pass in must be two items long."
        self.final_substitutions.remove(substitution)

    def get_final_substitutions(self):
        """Returns the list of final substitutions that are performed by the text generator
        before returning the text. Just a quick index into a variable in the object
        namespace.
        """
        return self.final_substitutions

    def set_final_substitutions(self, substitutions):
        """Set the list of final substitutions that are performed on generated text before
        it's returned. SUBSTITUTIONS must be a list of two-item lists, of the form
        [regex to search for, replacement], as in the default list in the __init__()
        method for the class.
        """
        for sublist in substitutions:       # Do some basic error-checking
            assert isinstance(sublist, (list, tuple)), "ERROR: substitution %s is not a list or tuple." % sublist
            assert len(sublist) == 2, "ERROR: substitution %s is not two items long." % sublist
        self.final_substitutions = substitutions

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
        """Train the model from a text file, or a list of text files supplied,
         as THE_FILES.
         """
        if isinstance(the_files, (str, bytes)): the_files = [ the_files ]
        assert isinstance(the_files, (list, tuple)), "ERROR: you cannot pass an object of type %s to %s.train" % (type(the_files), self)
        assert len(the_files) > 0, "ERROR: empty file list passed to %s.train()" % self
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
        log_it("        the_starts = %s." % self.chains.the_starts, 5)
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

    def _produce_text(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Actually generate some text. This is a generator function that produces (yields)
        one paragraph at a time. If you just need all the text at once, you might want
        to use the convenience wrapper gen_text() instead.
        """
        log_it("_produce_text() called.", 4)
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
            if random.random() <= paragraph_break_probability or which_sentence == sentences_desired - 1:
                the_text = th.multi_replace(the_text, self.final_substitutions)
                yield the_text.strip() + "\n"
                the_text = ""
        raise StopIteration

    def gen_text(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Generate the full amount of text required. This is just a convenience wrapper
        for _produce_text().
        """
        return '\n'.join(self._produce_text(sentences_desired, paragraph_break_probability))

    def gen_html_frag(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Produce the same text that _produce_text would, but wrapped in HTML <p></p> tags."""
        log_it("We're generating an HTML fragment.", 3)
        the_text = self._produce_text(sentences_desired, paragraph_break_probability)
        return '\n\n'.join(['<p>%s</p>' % p.strip() for p in the_text])

    def print_text(self, sentences_desired, paragraph_break_probability=0.25, pause=0, columns=-1):
        """Prints generated text directly to stdout."""
        for t in self._produce_text(sentences_desired, paragraph_break_probability):
            time_now = time.time()

            if columns == 0:  # Wrapping is totally disabled. Print exactly as generated.
                log_it("INFO: COLUMNS is zero; not wrapping text at all", 2)
                print(t)
            else:
                if columns == -1:  # Wrap to best guess for terminal width
                    log_it("INFO: COLUMNS is -1; wrapping text to best-guess column width", 2)
                    padding = 0
                else:  # Wrap to specified width (unless current terminal width is odd, in which case we're off by 1)
                    padding = max((th.terminal_width() - columns) // 2, 0)
                    log_it("INFO: COLUMNS is %s; padding text with %s spaces on each side" % (columns, padding), 2)
                    log_it("NOTE: terminal width is %s" % th.terminal_width())
                t = th.multi_replace(t, [['\n\n', '\n'], ])     # Last chance to postprocess text is right here
                for the_paragraph in t.split('\n'):
                    if the_paragraph:                   # Skip any empty paragraphs that may pop up
                        th.print_indented(the_paragraph, each_side=padding)
                        print()
            time.sleep(max(pause - (time.time() - time_now), 0))    # Pause until it's time for a new paragraph.


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

def main(**kwargs):
    """Handle the main program loop and generate some text.

    By default, this routine can simply be called as main(), with no arguments; this
    is what happens when the script is called from the command line. In this case,
    it parses the arguments passed on the command line. However, for testing
    purposes, it can also be called with keyword arguments in the same format that
    the command line would be parsed, i.e. with something like

        main(markov_length=2, input=['Song of Solomon.txt'], count=20, chars=True)
    """
    if (not sys.stdout.isatty()) and (patrick_logger.verbosity_level < 1):  # Assume we're running on a web server. ...
        print_html_docs()

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
    log_it('INFO: Command-line options parsed; parameters are: %s' % pprint.pformat(opts), 2)
    patrick_logger.verbosity_level = opts['verbose'] - opts['quiet']
    log_it('DEBUGGING: verbosity_level after parsing command line is %d.' % patrick_logger.verbosity_level, 2)

    # Now instantiate and train the model, and save the compiled chains, if that's what the user wants
    print()                     # Cough up a blank line at the beginning.
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
        print(the_text)
    else:
        genny.print_text(sentences_desired=opts['count'], pause=opts['pause'], columns=opts['columns'])


if __name__ == "__main__":
    if force_test:
        main(count=20, load='/lovecraft/corpora/previous/Beyond the Wall of Sleep.2.pkl', html=False, pause=1)
    else:
        main()
