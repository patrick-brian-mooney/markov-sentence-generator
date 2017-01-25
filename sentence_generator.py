#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Patrick Mooney's Markov sentence generator: generates random (but often
intelligible) text based on a frequency analysis of one or more existing texts.
It is based on Harry R. Schwartz's Markov sentence generator, but is intended
to be more flexible for use in other projects (primarily my automated text blog,
UlyssesRedux). Licensed under the GPL v3+. Available at
https://github.com/patrick-brian-mooney/markov-sentence-generator. See README.md
for more details.

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
  starts, the_mapping = buildMapping(word_list('somefile.txt'), markov_length=2)
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
      chains are notably larger than the individual files.

      This option does NOT specify an output file into which the generated text
      is saved. To do that, use shell redirection, e.g. by doing:

          ./sentence_generator -i somefile.txt > outputfile.txt

  -c NUM, --count=NUM
      Specify how many sentences the script should generate. (If unspecified,
      the default number of sentences to generate is one.)

  -w NUM, --columns=NUM
      Currently unimplemented.

  -p NUM, --pause=NUM
      Currently unimplemented.

  --html
      Wrap paragraphs of text output by the program with HTML paragraph tags.
      It does NOT generate a complete, formally valid HTML document (which
      would involve generating a heading and title, among other things), but
      rather generates an HTML fragment that you can insert into another HTML
      document, as you wish.

This program is licensed under the GPL v3 or, at your option, any later
version. See the file LICENSE.md for a copy of this licence.
"""

import re, random, sys, pickle, getopt, pprint

import text_handling as th  # https://github.com/patrick-brian-mooney/python-personal-library/blob/master/text_handling.py
import patrick_logger       # From https://github.com/patrick-brian-mooney/personal-library
from patrick_logger import log_it

# Set up some constants
patrick_logger.verbosity_level = 0  # Bump above zero to get more verbose messages about processing and to skip the
                                    # "are we running on a webserver?" check.

punct_with_space_after = r'.,\:!?;'
sentence_ending_punct = r'.!?'
punct_with_no_space_before = r'.,!?;—․-:/'
punct_with_no_space_after = r'—-/․'             # Note: that last character is U+2024, "one-dot leader".
word_punct = r"'’❲❳%°#․$"                       # Punctuation marks to be considered part of a word.
token_punct = r".,\:\-!?;—\/&"                  # These punctuation marks also count as tokens.

final_substitutions = [                 # list of lists: each [search_regex, replace_regex]. Substitutions occur in order specified.
    ['--', '—'],
    ['\.\.\.', '…'],
    ['․', '.'],                         # replace one-dot leader with period
    ['\.\.', '.'],
    [" ' ", ''],
    ['―-', '―'],
    [':—', ': '],
    ["\n' ", '\n'],                     # newline--single quote--space
    ["<p>'", '<p>'],
    ["<p> ", '<p>'],                    # <p>-space to <p> (without space)
    ["<p></p>", ''],                    # <p></p> to nothing
    ['- ', '-'],
    ['—-', '—'],                        # em dash-hyphen to em dash
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
    it's a convenience function for code that calls this code.

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
    """Print a usage message to the terminal"""
    patrick_logger.log_it("INFO: print_usage() was called", 2)
    print('\n\n')
    print(__doc__)

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

def word_list_from_string(the_string):
    """Converts a string into a set of tokens."""
    return [fix_caps(w) for w in re.findall(r"[\w%s]+|[%s]" % (word_punct, token_punct), the_string)]

def word_list(filename):
    """Reads  the contents of the file FILENAME and splits it into into a list of
    tokens -- words and (some) punctuation.
    """
    with open(filename, 'r') as the_file:
        return word_list_from_string(the_file.read())

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

def buildMapping(word_list, markov_length):
    """Build and normalize the_mapping."""
    the_temp_mapping = {}
    the_mapping = {}
    starts = []
    starts.append(word_list[0])
    for i in range(1, len(word_list) - 1):
        if i <= markov_length:
            history = word_list[: i + 1]
        else:
            history = word_list[i - markov_length + 1 : i + 1]
        follow = word_list[i + 1]
        # if the last elt was a sentence-ending punctuation, add the next word to the start list
        if history[-1] in sentence_ending_punct and follow not in punct_with_space_after:
            starts.append(follow)
        addItemToTempMapping(history, follow, the_temp_mapping)
    # Normalize the values in the_temp_mapping, put them into mapping
    for first, followset in the_temp_mapping.items():
        total = sum(followset.values())
        # Normalizing here:
        the_mapping[first] = dict([(k, v / total) for k, v in followset.items()])
    return starts, the_mapping

def next(prevList, the_mapping):
    """Returns the next word in the sentence (chosen randomly),
    given the previous ones."""
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
    return retval

def genSentence(markov_length, the_mapping, starts, allow_single_character_sentences=False):
    """Build a sentence, starting with a random 'starting word.'

    MARKOV_LENGTH is the length of the chains used to generate the sentence, from
    1 to whatever the maximum sentence length is. Practically speaking, there's
    no point in setting it above the maximum length of sentences in the source
    text, and the USEFUL range of this parameter is probably noticeably below
    that level.

    THE_MAPPING is the chains dictionary compiled by buildMapping().

    STARTS is the list of possible sentence-beginning words compiled by
    buildMapping().

    ALLOW_SINGLE_CHARACTER_SENTENCES indicates whether sentences that consist
    entirely of a single character followed by sentence-ending punctuation
    should be rejected (if the parameter is False) or allowed (if the parameter
    is True).

    Returns a string, the generated sentence.
    """
    log_it("      genSentence() called.", 4)
    log_it("        markov_length = %d." % markov_length, 5)
    log_it("        the_mapping = %s." % the_mapping, 5)
    log_it("        starts = %s." % starts, 5)
    log_it("        allow_single_character_sentences = %s." % allow_single_character_sentences, 5)
    curr = random.choice(starts)
    sent = th.capitalize(curr)
    prevList = [curr]
    # Keep adding words until we hit a period, exclamation point, or question mark
    while curr not in sentence_ending_punct:
        curr = next(prevList, the_mapping)
        prevList.append(curr)
        # if the prevList has gotten too long, trim it
        while len(prevList) > markov_length:
            prevList.pop(0)
        if curr not in punct_with_no_space_before and (len(prevList) < 2 or prevList[-2] not in punct_with_no_space_after):
            sent += " " # Add spaces between words (but not punctuation)
        sent += curr
    if not allow_single_character_sentences:
        if len(sent.strip().strip(sentence_ending_punct).strip()) == 1:                             # If we got a one-character sentence ...
            if sent.strip().strip(sentence_ending_punct).strip().upper() != "I":                    # And that one character isn't "I" ...
                sent = genSentence(markov_length=markov_length, the_mapping=the_mapping, starts=starts) # Retry, recursively.
    return sent

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

def gen_text(the_mapping, starts, markov_length=1, sentences_desired=1, is_html=False, paragraph_break_probability = 0.25):
    """Actually generate the text."""
    log_it("gen_text() called.", 4)
    log_it("  Markov length is %d; requesting %d sentences." % (markov_length, sentences_desired), 4)
    log_it("  Legitimate starts: %s" % starts, 5)
    log_it("  Probability data: %s" % the_mapping, 5)
    if is_html:
        log_it("  -- and we're generating an HTML fragment.", 3)
        the_text = "<p>"
    else:
        the_text = ""
    if sentences_desired > 0:
        for which_sentence in range(0, sentences_desired):
            try:
                if the_text[-1] != "\n" and the_text[-3:] != "<p>":
                    the_text = the_text + " "   # Add a space to the end if we're not starting a new paragraph.
            except IndexError:
                pass        # If the string is so far empty, well, just move forward. We don't need to add a space to the beginning of the text, anyway.
            the_text = the_text + genSentence(markov_length, the_mapping, starts)
            if random.random() <= paragraph_break_probability:
                if is_html:
                    the_text = the_text.strip() + "</p>\n\n<p>"
                else:
                    the_text = the_text.strip() + "\n\n"
    if is_html:
        the_text = the_text + "</p>"
    the_text = th.multi_replace(the_text, final_substitutions)
    return the_text

def main():
    # Set up variables for this run
    if (not sys.stdout.isatty()) and (patrick_logger.verbosity_level < 1):  # Assume we're running on a web server. ...
        print('Content-type: text/html\n\n')                                # ... print HTTP headers, then documentation.
        print("""<!doctype html><html><head><title>Patrick Mooney's Markov chain–based text generator</title><link rel="profile" href="http://gmpg.org/xfn/11" /></head><body><h1>Patrick Mooney's Markov chain–based text generator</h1><p>Code is available <a rel="muse" href="https://github.com/patrick-brian-mooney/markov-sentence-generator">here</a>.</p><pre>%s</pre></body></html>"""% __doc__)
        sys.exit(0)
    markov_length = 1
    chains_file = ''
    starts = None
    the_mapping = None
    sentences_desired = 1
    inputs = [].copy()
    is_html = False
    # Next, parse command-line options, if there are any
    if len(sys.argv) > 1: # The first item in argv, of course, is the name of the program itself.
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'vhqo:l:c:w:p:i:m:',
                    ['verbose', 'help', 'quiet', 'output=', 'load=', 'count=',
                    'columns=', 'pause=', 'html', 'input=', 'markov-length='])
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
                log_it('INFO: %s invoked, added one to verbosity level\n     Verbosity level is now %d.' % (opt, patrick_logger.verbosity_level))
            elif opt in ('-q', '--quiet'):
                log_it('INFO: %s invoked, decreasing verbosity level by one\n     Verbosity level is about to drop to %d.' % (opt, patrick_logger.verbosity_level-1))
                patrick_logger.verbosity_level -= 1
            elif opt in ('-m', '--markov-length'):      # Length of Markov chains generated. Incompatible with -l.
                log_it("INFO: -m invoked, argument is %s." % args, 1)
                if starts == None and the_mapping == None:
                    markov_length = int(args)
                else:
                    log_it("ERROR: If you load previously generated chains with -l, that file specifies the\nMarkov chain length. It cannot be overriden with -m or --markov-length.")
                    sys.exit(2)
            elif opt in ('-o', '--output'):
                chains_file = args          # Specify output file for compiled chains.
            elif opt in ('-l', '--load'):   # Load compiled chains.
                if markov_length == 1:
                    markov_length, the_starts, the_mapping = read_chains(args)
                else:
                    log_it("ERROR: you cannot both specify a chains file with -m and also load a chains file\nwith -l. If you specify a file with -l, that file contains the chain length.")
                    sys.exit(2)
            elif opt in ('-c', '--count'):
                sentences_desired = int(args)    # How many sentences to generate (0 is "keep working until interrupted").
            elif opt in ('-i', '--input'):
                log_it("  -i specified with argument %s." % args)
                inputs.append(args)
            elif opt in ('-w', '--columns'):
                pass    # How many columns wide the output should be. Currently unimplemented.
            elif opt in ('-p', '--pause'):
                pass    # How many seconds to pause between paragraphs. Currently unimplemented.
            elif opt == '--html':
                is_html = True    # Wrap paragraphs of text that are output in <p> ... </p>.
    else:
        log_it('DEBUGGING: No command-line parameters', 2)
        print_usage()
    log_it('DEBUGGING: verbosity_level after parsing command line is %d.' % patrick_logger.verbosity_level, 2)
    if starts == None or the_mapping == None:     # then no chains file was loaded.
        log_it("INFO: No chains file specified; parsing text files specified.", 1)
        log_it("  ... input files specified are %s." % inputs, 1)
        all_words = [].copy()
        for the_file in inputs:
            log_it("    ... processing file %s." % the_file, 2)
            all_words += word_list(the_file)
            log_it("       ... all_words now contains %d words." % len(all_words), 2)
        if all_words:
            starts, the_mapping = buildMapping(all_words, markov_length)
            if chains_file:
                store_chains(markov_length, starts, the_mapping, chains_file)
    if starts == None or the_mapping == None:     # Ridiculous! We must have SOMETHING to work with.
        log_it("ERROR: You must either specify a chains file with -l, or else at least one text file with -i.")
        sys.exit(2)
    print(gen_text(the_mapping, starts, markov_length, sentences_desired, is_html))

if __name__ == "__main__":
    main()
