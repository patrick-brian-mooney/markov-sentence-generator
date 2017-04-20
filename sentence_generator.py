#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Patrick Mooney's Markov sentence generator, %s.

This program generates random (but often intelligible) text based on a
frequency analysis of one or more existing texts. It is based on Harry R.
Schwartz's Markov sentence generator, but is intended to be more flexible for
use in my various text-generation projects. Licensed under the GPL v3+.

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



COMMAND-LINE OPTIONS

  -h, --help
      Display this help message.

  -v, --verbose
      Increase the verbosity of the script, i.e. get more output. Can be
      specified multiple times to make the script more and more verbose.
      Current verbosity levels are subject to change in future versions
      of the script.

  -q, --quiet
      Decrease the verbosity of the script. You can mix -v and -q, bumping the
      verbosity level up and down as the command line is processed, but really,
      what are you doing with your life?

  -m NUM, --markov-length=NUM
      Length (in words) of the Markov chains used by the program. Longer chains
      generate text "more like the original text" in many ways, (often)
      including perceived grammatical correctness; but using longer chains also
      means that the sentences generated "are less random," take longer to
      generate and work with, and take more memory (and disk space) to store.
      Optimal values depend on the source text and its characteristics, but you
      might reasonably experiment with numbers from 1 to 4 to see what you get.
      Larger numbers will increasingly result in the script just coughing up
      whole sentences from the original source texts, which may or may not be
      what you want.

      You cannot specify a chain length with this option if you are loading
      generated probability data from a previous run with -l or --load, because
      the probability data was compiled with chains of a certain length on that
      previous run, and that length is the length that will be used when you
      load the data. If you need to use a different chain length, you also need
      to re-generate the probability data by re-loading the  original source files
      with -i or --input.

      The default Markov chain length, if not overridden with this parameter,
      is one.

  -i FILENAME, --input=FILENAME
      Specify an input file to use as the basis of the generated text. You can
      specify this parameter more than once; all of the files specified will be
      treated as if they were one long file containing all of the text in all
      of the input files. If you are going to be regularly calling the script
      with the same input files, consider saving the probability data with -o,
      then loading that data with -l on subsequent runs; loading pre-compiled
      probability data with -l is much faster than re-generating it with -i.

      You can specify -i or --input multiple times, but you cannot use both
      -i / --input and -l / --load: you need to EITHER load pre-generated
      probability data, OR ELSE generate it fresh from plain-text files. (The
      reason for this is that, once all of the input files have been processed,
      the program discards some data that would be necessary to combine the
      file with other files in order to process the chains more efficiently,
      and it is these postprocessed chains that are saved with -o / --output.)

      sentence_generator.py ONLY understands PLAIN TEXT files (not HTML. not
      markdown. not Microsoft Word. not mailbox files. not RTF. Just plain
      text). Trying to feed it anything else will either fail or produce
      unpredictable results. You've been warned.

  -l FILE, --load=FILE
      Load generated probability data ("chains") from a previous run that have
      been saved with -o or --output.  Doing so is faster than re-generating
      the data, so if you're going to be using the same data a lot, you can
      save time by generating the data once.

      You cannot both load probability chains and specify input files with (-i
      or --input); do one or the other. You also cannot use the -l or --load
      option more than once. Finally, you also cannot specify a Markov chain
      length (with -m or --markov-length) when loading probability data with
      this option, because the generated probability data forces the use of
      chains of the same length as were specified with the data was initially
      generated.

  -o FILE, --output=FILE
      Specify a file into which the generated probability data (the "chains")
      should be saved. If you're going to be using the same data repeatedly,
      saving the data and then re-loading it with the -l option is faster than
      re-generating the data on every run by specifying the same input files
      with -i. However, if the Markov length is greater than 1, the generated
      chains are notably larger than the source files.

      This option does NOT specify an output file into which the generated text
      is saved. To do that, use shell redirection, e.g. by doing:

          ./sentence_generator -i somefile.txt > outputfile.txt

  -c NUM, --count=NUM
      Specify how many sentences the script should generate. (If unspecified,
      the default number of sentences to generate is one.)

  -r, --chars
      By default, the individual tokens in the chains generated by this program
      are whole words; chances are that this is what most people playing with a
      Markov chain-based text generator want most of the time anyway.

      However, if you specify -h or --chars, the tokens in the Markov chains are
      individual characters instead of words, and these individual characters
      are recombined to form random words, instead of words being recombined to
      form random sentences.

      Doing this will certainly increase the degree to which the generated text
      is "gibberishy," especially if you don't bump up the chain length with -m
      or --markov-length.

  -w NUM, --columns=NUM
      Wrap the output to NUM columns.

      If NUM is -1 (or not specified), the sentence generator does its best to
      wrap to the width of the current terminal. If NUM is 0, no wrapping at
      all is performed, and words may be split between lines.

      This option cannot be used with --html.

  -p NUM, --pause=NUM
      Pause NUM seconds after every paragraph is printed.

      This option cannot be used with --html.

      Not yet working, but will work in v2.0.

  --html
      Wrap paragraphs of text output by the program with HTML paragraph tags.
      It does NOT generate a complete, formally valid HTML document (which
      would involve generating a heading and title, among other things), but
      rather generates an HTML fragment that you can insert into another HTML
      document, as you wish.

This program is licensed under the GPL v3 or, at your option, any later
version. See the file LICENSE.md for a copy of this licence.
"""

__author__ = "Patrick Mooney, http://patrickbrianmooney.nfshost.com/~patrick/"
__version__ = "$v2.0 $"
__date__ = "$Date: 2017/04/19 16:16:00 $"
__copyright__ = "Copyright (c) 2015-17 Patrick Mooney"
__license__ = "GPL v3, or, at your option, any later version"

import re, random, sys, pickle, getopt, pprint, time

import text_handling as th          # From  https://github.com/patrick-brian-mooney/personal-library
import patrick_logger               # From  https://github.com/patrick-brian-mooney/personal-library
from patrick_logger import log_it

# Set up some constants
patrick_logger.verbosity_level = 2  # Bump above zero to get more verbose messages about processing and to skip the
                                    # "are we running on a webserver?" check.

force_test = True
paragraph_pause = 0

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

# Schwartz's version stored mappings globally to save copying time, but this
# makes the code less flexible for my purposes; still, I've kept his
# declarations for the global variables here, where the variables were
# previously declared.

# the_temp_mapping: initially an empty dictionary, {}
# (tuple of words) -> {dict: word -> number of times the word appears following the tuple}
# Example entry:
#    ('eyes', 'turned') => {'to': 2.0, 'from': 1.0}
# Used briefly while first constructing the normalized mapping

# the_mapping: initially an empty dictionary, {}
# (tuple of words) -> {dict: word -> *normalized* number of times the word appears following the tuple}
# Example entry:
#    ('eyes', 'turned') => {'to': 0.66666666, 'from': 0.33333333}

# starts: a list of words that can begin sentences. Initially an empty list, []
# Contains the set of words that can start sentences


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

def print_usage():
    """Print a usage message to the terminal."""
    patrick_logger.log_it("INFO: print_usage() was called", 2)
    print('\n\n')
    print(__doc__ % __version__.strip('$').strip())

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

def to_hash_key(lst):
    """Tuples can be hashed; lists can't.  We need hashable values for dict keys.
    This looks like a hack (and it is, a little) but in practice it doesn't
    affect processing time too negatively."""
    return tuple(lst)

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

def store_chains(markov_length, the_starts, the_mapping, filename):
    """Shove the relevant chain-based data into a dictionary, then pickle it and
    store it in the designated file.
    """
    chains_dictionary = { 'markov_length': markov_length, 'the_starts': the_starts, 'the_mapping': the_mapping }
    try:
        the_chains_file = open(filename, 'wb')
        the_pickler = pickle.Pickler(the_chains_file, protocol=-1)    # Use the most efficient protocol possible
        the_pickler.dump(chains_dictionary)
        the_chains_file.close()
    except IOError as e:
        log_it("ERROR: Can't write chains to %s; the system said '%s'." % (filename, str(e)), 0)
    except pickle.PickleError as e:
        log_it("ERROR: Can't write chains to %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0)

def read_chains(filename):
    """Read the pickled chain-based data from a chains file."""
    try:
        the_chains_file = open(filename, 'rb')
        chains_dictionary = pickle.load(the_chains_file)
        the_chains_file.close()
    except IOError as e:
        log_it("ERROR: Can't read chains from %s; the system said '%s'." % (filename, str(e)), 0)
    except pickle.PickleError as e:
        log_it("ERROR: Can't read chains from %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0)
    return chains_dictionary['markov_length'], chains_dictionary['the_starts'], chains_dictionary['the_mapping']


class MarkovChainTextModel(object):
    """Chains representing a model of a text."""
    def __init__(self):
        """Instantiate a new, empty set of chains."""
        self.starts = None              # List of tokens allowed at the beginning of a sentence.
        self.markov_length = 0          # Length of the chains.
        self.the_mapping = None         # Dictionary representing the Markov chains.
        self.character_tokens = False   # True if the chains are characters, False if they are words. 


class TextGenerator(object):
    """A general-purpose text generator. To use it, instantiate it, train it, and
    then have it generate text.
    """
    def __init__(self, name=None):
        """Create a new instance."""
        self.name = name                                # NAME is totally optional and entirely for your benefit.
        self.chains = MarkovChainTextModel()            # Markov chain-based representation of the text(s) used to train this generator.
        self.allow_single_character_sentences = False   # Is this model allowed to produce one-character sentences? 

    def __repr__(self):
        if self.is_trained():
            return '< class %s, named "%s", with Markov length %d >' % (self.__class__, self.name, self.chains.markov_length)
        else:
            return '< class %s, named "%s", UNTRAINED >' % (self.__class__, self.name)

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
            addItemToTempMapping(history, follow, the_temp_mapping)
        # Now, normalize the values in the_temp_mapping and put them into the_mapping
        for first, followset in the_temp_mapping.items():
            total = sum(followset.values())
            the_mapping[first] = dict([(k, v / total) for k, v in followset.items()])   # Here's the normalizing step.
        self.chains.starts = starts
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
        return (self.chains.starts and self.chains.the_mapping and self.chains.markov_length)

    def train(self, the_text, markov_length=1, character_tokens=False):
        """Train the model by getting it to analyze a text passed in."""
        self._build_mapping(self._token_list(the_text, character_tokens=character_tokens),
                            markov_length=markov_length, character_tokens=character_tokens)

    def _gen_sentence(self):
        """Build a sentence, starting with a random 'starting word.' Returns a string,
        which is the generated sentence.
        """
        log_it("      _gen_sentence() called.", 4)
        log_it("        markov_length = %d." % self.chains.markov_length, 5)
        log_it("        the_mapping = %s." % self.chains.the_mapping, 5)
        log_it("        starts = %s." % self.chains.starts, 5)
        log_it("        allow_single_character_sentences = %s." % self.allow_single_character_sentences, 5)
        curr = random.choice(self.chains.starts)
        sent = curr
        prevList = [curr]
        # Keep adding words until we hit a period, exclamation point, or question mark
        while curr not in sentence_ending_punct:
            curr = next(prevList, self.chains.the_mapping)
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
                    sent = _gen_sentence(markov_length=markov_length, the_mapping=the_mapping, starts=starts)    # Retry, recursively.
        return th.capitalize(sent)

    def gen_text(self, sentences_desired=1, paragraph_break_probability=0.25):
        """Actually generate some text."""
        log_it("gen_text() called.", 4)
        log_it("  Markov length is %d; requesting %d sentences." % (self.chains.markov_length, sentences_desired), 4)
        log_it("  Legitimate starts: %s" % self.chains.starts, 5)
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
        
    def gen_html_frag(sentences_desired=1, paragraph_break_probability=0.25):
        """Produce the same text that gen_text would, but wrapped in HTML <p></p> tags."""
        log_it("We're generating an HTML fragment.", 3)
        the_text = self.gen_text(sentences_desired, paragraph_break_probability)
        return '\n\n'.join(['<p>%s</p>' % p for p in the_text.split('\n\n')])        


def main(markov_length=1,
         chains_file='',
         starts=None,
         the_mapping=None,
         sentences_desired=1,
         inputs=[][:],
         character_tokens=False,
         is_html=False,
         columns=-1):

    """Parse command-line options and generate some text.
    """

    global paragraph_pause
    # Set up variables for this run
    if (not sys.stdout.isatty()) and (patrick_logger.verbosity_level < 1):  # Assume we're running on a web server. ...
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
    # Next, parse command-line options, if there are any
    if len(sys.argv) > 1: # The first item in argv, of course, is the name of the program itself.
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'vhqro:l:c:w:p:i:m:',
                    ['verbose', 'help', 'quiet', 'output=', 'load=', 'count=',
                    'columns=', 'pause=', 'chars', 'html', 'input=', 'markov-length='])
            log_it('INFO: options returned from getopt.getopt() are: ' + pprint.pformat(opts), 2)
        except getopt.GetoptError:
            log_it('ERROR: Bad command-line arguments; exiting to shell')
            print_usage()
            sys.exit(2)
        log_it('INFO: detected number of command-line arguments is %d.' % len(sys.argv), 2)
        for opt, args in opts:
            log_it('Processing option %s.' % opt, 2)
            if opt in ('-h', '--help'):
                log_it('INFO: %s invoked, printing usage message.' % opt)
                print_usage()
                sys.exit()
            elif opt in ('-v', '--verbose'):
                patrick_logger.verbosity_level += 1
                log_it('INFO: %s invoked, added one to verbosity level\n     Verbosity level is now %d.' %
                       (opt, patrick_logger.verbosity_level))
            elif opt in ('-q', '--quiet'):
                log_it('INFO: %s invoked, decreasing verbosity level by one\n     Verbosity level is about to drop to %d.' %
                       (opt, patrick_logger.verbosity_level-1))
                patrick_logger.verbosity_level -= 1
            elif opt in ('-m', '--markov-length'):      # Length of Markov chains generated. Incompatible with -l.
                log_it("INFO: -m invoked, argument is %s." % args, 1)
                if starts == None and the_mapping == None:
                    markov_length = int(args)
                else:
                    log_it("ERROR: If you load previously generated chains with -l, that file specifies the\nMarkov "
                           "chain length. It cannot be overriden with -m or --markov-length.")
                    sys.exit(2)
            elif opt in ('-o', '--output'):
                chains_file = args          # Specify output file for compiled chains.
            elif opt in ('-l', '--load'):   # Load compiled chains.
                if markov_length == 1:
                    markov_length, the_starts, the_mapping = read_chains(args)
                else:
                    log_it("ERROR: you cannot both specify a chains file with -m and also load a chains file\nwith -l. If you specify a file with -l, that file contains the chain length.")
                    sys.exit(2)
            elif opt in ('-r', '--chars'):
                log_it('INFO: %s invoked; using characters, not words, as the tokens in the chains' % opt, 2)
                character_tokens = True
            elif opt in ('-c', '--count'):
                sentences_desired = int(args)    # How many sentences to generate (0 is "keep working until interrupted").
            elif opt in ('-i', '--input'):
                log_it("  -i specified with argument %s." % args)
                inputs.append(args)
            elif opt in ('-w', '--columns'):
                columns = int(args)    # How many columns wide the output should be.
                is_html = False
            elif opt in ('-p', '--pause'):
                paragraph_pause = int(args)    # How many seconds to pause between paragraphs. Currently unimplemented.
                is_html = False
            elif opt == '--html':
                is_html = True    # Wrap paragraphs output text in <p> ... </p>.
                paragraph_pause = 0
                columns = 0
    else:
        if not force_test:
            log_it('DEBUGGING: No command-line parameters', 2)
            print_usage()
    log_it('DEBUGGING: verbosity_level after parsing command line is %d.' % patrick_logger.verbosity_level, 2)
    if starts == None or the_mapping == None:     # then no chains file was loaded.
        log_it("INFO: No chains file specified; parsing text files specified.", 1)
        log_it("  ... input files specified are %s." % inputs, 1)
        chain_tokens = [][:]
        for the_file in inputs:
            log_it("    ... processing file %s." % the_file, 2)
            chain_tokens += word_list(the_file, character_tokens=character_tokens)
            log_it("       ... chain_tokens now contains %d tokens." % len(chain_tokens), 2)
        if chain_tokens:
            starts, the_mapping = _build_mapping(chain_tokens, markov_length)
            if chains_file:
                store_chains(markov_length, starts, the_mapping, chains_file)
    if starts == None or the_mapping == None:     # Ridiculous! We must have SOMETHING to work with.
        log_it("ERROR: You must either specify a chains file with -l, or else at least one text file with -i.")
        sys.exit(2)

    the_text = gen_text(the_mapping=the_mapping, starts=starts, markov_length=markov_length, sentences_desired=sentences_desired, is_html=is_html, character_tokens=character_tokens)
    if columns == 0:         # Wrapping is totally disabled. Print exactly as generated.
        log_it("INFO: COLUMNS is zero; not wrapping text at all", 2)
        print(the_text)
        sys.exit(0)
    elif columns == -1:
        log_it("INFO: COLUMNS is -1; wrapping text to best-guess column width", 2)
        padding = 0
    else:
        padding = max((th.terminal_width() - columns) // 2, 0)
        log_it("INFO: COLUMNS is %s; padding text with %s spaces on each side" % (columns, padding), 2)
        log_it("NOTE: terminal width is %s" % th.terminal_width())
    the_text = th.multi_replace(the_text, [['\n\n', '\n']])
    for the_paragraph in the_text.split('\n'):
        th.print_indented(the_paragraph, each_side=padding)
        print()


if __name__ == "__main__":
    if force_test:
        import glob
        main(markov_length=4, sentences_desired=20, columns=76, inputs=glob.glob('/lovecraft/corpora/previous/*txt'), character_tokens=True)
    else:
        main()
