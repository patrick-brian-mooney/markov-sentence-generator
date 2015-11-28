#!/usr/bin/python3

import re
import random
import sys
import pickle

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
        print("ERROR: Can't write chains to %s; the system said '%s'." % (filename, str(e)))
    except pickle.PickleError as e:
        print("ERROR: Can't write chains to %s because a pickling error occurred; the system said '%s'." % (filename, str(e))) 

def read_chains(filename):
    """Shove the relevant chain-based data into a dictionary, then pickle it and store
    it in the designated file."""
    try:
        the_chains_file = open(filename, 'rb')
        # the_pickler = pickle.Pickler(the_chains_file, protocol=-1)    # Use the most efficient protocol possible, even if not readable by earlier Pythons
        chains_dictionary = pickle.load(the_chains_file)
        the_chains_file.close()
    except IOError as e:
        print("ERROR: Can't read chains from %s; the system said '%s'." % (filename, str(e)))
    except pickle.PickleError as e:
        print("ERROR: Can't read chains from %s because a pickling error occurred; the system said '%s'." % (filename, str(e))) 
    return chains_dictionary['markov_length'], chains_dictionary['the_starts'], chains_dictionary['the_mapping']

def main():
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: ' + sys.argv[0] + ' text_source [chain_length=1]\n')
        sys.exit(1)

    filename = sys.argv[1]
    markov_length = 1
    if len(sys.argv) == 3:
        markov_length = int(sys.argv[2])

    starts, the_mapping = buildMapping(word_list(filename), markov_length)
    print(genSentence(markov_length, the_mapping, starts))

if __name__ == "__main__":
    main()
