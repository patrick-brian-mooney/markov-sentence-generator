#!/usr/bin/python3
"""Patrick Mooney's Markov sentence generator, based on Harry R. Schwartz's
Markov sentence generator. Licensed under the GPL v3+. Available on GitHub at
https://github.com/patrick-brian-mooney/markov-sentence-generator. See
README.md for more details.
"""

import re
import random
import sys
import pickle
import getopt
import pprint

import patrick_logger
from patrick_logger import log_it, verbosity_level # From https://github.com/patrick-brian-mooney/personal-library


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

patrick_logger.verbosity_level = 0

def fix_caps(word):
    """We want to be able to compare words independent of their capitalization."""
    # Ex: "FOO" -> "foo"
    if word.isupper() and word != "I":
        word = word.lower()
        # Ex: "LaTeX" => "Latex"
    elif word[0].isupper():
        word = word.lower().capitalize()
        # Ex: "wOOt" -> "woot"
    else:
        word = word.lower()
    return word

def to_hash_key(lst):
    """Tuples can be hashed; lists can't.  We need hashable values for dict keys.
    This looks like a hack (and it is, a little) but in practice it doesn't
    affect processing time too negatively."""
    return tuple(lst)

def word_list(filename):
    """Returns the contents of the file, split into a list of words and
    (some) punctuation."""
    the_file = open(filename, 'r')
    word_list = [fix_caps(w) for w in re.findall(r"[\w']+|[.,!?;]", the_file.read())]
    the_file.close()
    return word_list

def addItemToTempMapping(history, word, the_temp_mapping):
    '''Self-explanatory -- adds "word" to the "the_temp_mapping" dict under "history".
    the_temp_mapping (and the_mapping) both match each word to a list of possible next
    words.
    Given history = ["the", "rain", "in"] and word = "Spain", we add "Spain" to
    the entries for ["the", "rain", "in"], ["rain", "in"], and ["in"].'''
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
    """Building and normalizing the_mapping."""
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
        # if the last elt was a period, add the next word to the start list
        if history[-1] == "." and follow not in ".,!?;":
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
    while to_hash_key(prevList) not in the_mapping:
        prevList.pop(0)
    # Get a random word from the_mapping, given prevList
    for k, v in the_mapping[to_hash_key(prevList)].items():
        sum += v
        if sum >= index and retval == "":
            retval = k
    return retval

def genSentence(markov_length, the_mapping, starts):
    '''Start with a random "starting word"'''
    log_it("genSentence() called.", 2)
    log_it("  markov_length = %d." % markov_length, 4)
    log_it("  the_mapping = %s." % the_mapping, 4)
    log_it("  starts = %s." % starts, 4)
    curr = random.choice(starts)
    sent = curr.capitalize()
    prevList = [curr]
    # Keep adding words until we hit a period
    while curr not in ".":
        curr = next(prevList, the_mapping)
        prevList.append(curr)
        # if the prevList has gotten too long, trim it
        if len(prevList) > markov_length:
            prevList.pop(0)
        if curr not in ".,!?;":
            sent += " " # Add spaces between words (but not punctuation)
        sent += curr
    return sent

def store_chains(markov_length, the_starts, the_mapping, filename):
    """Shove the relevant chain-based data into a dictionary, then pickle it and store
    it in the designated file."""
    chains_dictionary = { 'markov_length': markov_length, 'the_starts': the_starts, 'the_mapping': the_mapping }
    try:
        the_chains_file = open(filename, 'wb')
        the_pickler = pickle.Pickler(the_chains_file, protocol=-1)    # Use the most efficient protocol possible, even if not readable by earlier Pythons
        the_pickler.dump(chains_dictionary)
        the_chains_file.close()
    except IOError as e:
        log_it("ERROR: Can't write chains to %s; the system said '%s'." % (filename, str(e)), 0)
    except pickle.PickleError as e:
        log_it("ERROR: Can't write chains to %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0) 

def read_chains(filename):
    """Shove the relevant chain-based data into a dictionary, then pickle it and store
    it in the designated file."""
    try:
        the_chains_file = open(filename, 'rb')
        chains_dictionary = pickle.load(the_chains_file)
        the_chains_file.close()
    except IOError as e:
        log_it("ERROR: Can't read chains from %s; the system said '%s'." % (filename, str(e)), 0)
    except pickle.PickleError as e:
        log_it("ERROR: Can't read chains from %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0) 
    return chains_dictionary['markov_length'], chains_dictionary['the_starts'], chains_dictionary['the_mapping']

def print_usage():
    """Print a usage message. Currently, nothing here."""
    pass

def main():
    # Set up variables for this run
    markov_length = 1
    chains_file = ''
    starts = None
    the_mapping = None
    sentences_desired = 0
    inputs = [].copy()
    # First, parse command-line options, if there are any
    if len(sys.argv) > 1: # The first option in argv, of course, is the name of the program itself.
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'vhqo:l:c:w:p:i:m:', ['verbose', 'help', 'quiet', 'output=', 'load=', 'count=', 'columns=', 'pause=', 'html', 'input=', 'markov-length='])
            log_it('INFO: options returned from getopt.getopt() are: ' + pprint.pformat(opts), 2)
        except getopt.GetoptError:
            log_it('ERROR: Bad command-line arguments; exiting to shell')
            print_usage()
            sys.exit(2)
        log_it('INFO: detected number of command-line arguments is %d.' % len(sys.argv), 2)
        for opt, args in opts:
            log_it('Processing option ' + str(opt), 2)
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
                    log_it("ERROR: you cannot both specify a chains file with -m and also load a chains file\nwith -l. If you specify -l, that file contains the Markov chain length.")
                    sys.exit(2)     
            elif opt in ('-c', '--count'):
                sentences_desired = args    # How many sentences to generate (0 is "keep working until interrupted").
            elif opt in ('-i', '--input'):
                log_it("  -i specified with argument %s." % args)
                inputs.append(args)
            elif opt in ('-w', '--columns'):
                pass    # How many columns wide the output should be. Currently unimplemented.
            elif opt in ('-p', '--pause'):
                pass    # How many seconds to pause between paragraphs. Currently unimplemented.
            elif opt == '--html':
                pass    # Output HTML instead of plain text. Currently unimplemented.
    else:
        log_it('DEBUGGING: No command-line parameters', 2)
    
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
    if starts == None or the_mapping == None:     # Ridiculous! We must have SOMETHING to work with
        log_it("ERROR: You must specify a chains file with -l, or else at least one text file with -i.")
        sys.exit(2)
    print(genSentence(markov_length, the_mapping, starts))

if __name__ == "__main__":
    main()
