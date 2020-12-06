#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A utility unit that generates new text based on Markov chains created from one
or more source texts. THIS unit is a stripped-down version of my own more
full-featured text generator, which is in turn based on code by HR Schwartz;
my more full-featured code is available at

https://github.com/patrick-brian-mooney/markov-sentence-generator

and a link to Schwartz's original source is available in the same place. Note
that the full-featured version is required to GENERATE files that this module
can only INTERPRET. That is: this stripped-down version is a utility for
projects that need to generate text based on pre-generated chains, but don't
need the additional features provided by the larger model.
"""


import pickle, random, sys


punct_with_space_after = r'.,\:!?;'
sentence_ending_punct = r'.!?'
punct_with_no_space_before = r'.,!?;—․-:/'
punct_with_no_space_after = r'—-/․'


def to_hash_key(lst):
    return tuple(lst)

def _find_first_alphanumeric(w):
    for i, c in enumerate(w):
        if c.isalpha() or c.isnumeric():
            return i
    return -1

def capitalize(w):
    if len(w) < 2: return w
    f = _find_first_alphanumeric(w)
    if f == -1:
        return w
    else:
        return w[:f] + w[f].upper() + w[1 + f:]


class MarkovChainTextModel(object):
    def __init__(self, filename):
        try:
            with open(filename, 'rb') as the_chains_file:
                chains_dictionary = pickle.load(the_chains_file)
        except IOError as e:
            print("ERROR: Can't read chains from %s; the system said '%s'." % (filename, e))
            sys.exit(1)
        except pickle.PickleError as e:
            print("ERROR: Can't read chains from %s because a pickling error occurred; the system said '%s'." % (filename, e))
            sys.exit(2)
        self.markov_length = chains_dictionary['markov_length']
        self.the_starts = chains_dictionary['starts']
        self.the_mapping = chains_dictionary['the_mapping']
        self.character_tokens = chains_dictionary['character_tokens']
        assert not self.character_tokens, "ERROR: this script cannot interpret 'character token' Markov chain files."


class TextGenerator(object):
    def __init__(self, chainsfile, name=None):
        self.name = name
        self.chains = MarkovChainTextModel(chainsfile)

    def __str__(self):
        if self.name:
            return '< class %s, named "%s", with Markov length %d >' % (self.__class__, self.name, self.chains.markov_length)
        else:
            return '< class %s (unnamed instance), with Markov length %d >' % (self.__class__, self.chains.markov_length)


    def next(self, prevList, the_mapping):
        prevList = [ p for p in prevList ]
        sum = 0.0
        retval = ""
        index = random.random()
        try:
            while to_hash_key(prevList) not in the_mapping:
                prevList.pop(0)
        except IndexError:
            retval = "."
        else:
            for k, v in the_mapping[to_hash_key(prevList)].items():
                sum += v
                if sum >= index and retval == "":
                    retval = k
                    break
        return retval

    def is_trained(self):
        return (self.chains.the_starts and self.chains.the_mapping and self.chains.markov_length)

    def _gen_sentence(self):
        curr = random.choice(self.chains.the_starts)
        sent = curr
        prevList = [curr]
        while curr not in sentence_ending_punct:
            curr = self.next(prevList, self.chains.the_mapping)
            prevList.append(curr)
            while len(prevList) > self.chains.markov_length:
                prevList.pop(0)
            if curr not in punct_with_no_space_before:
                if (len(prevList) < 2 or prevList[-2] not in punct_with_no_space_after):
                    sent += " "
            sent += curr
        if len(sent.strip().strip(sentence_ending_punct).strip()) == 1:
            if sent.strip().strip(sentence_ending_punct).strip().upper() != "I":
                sent = self._gen_sentence()
        return capitalize(sent)

    def _produce_text(self, sentences_desired=1, paragraph_break_probability=0.25):
        the_text = ""
        for which_sentence in range(0, sentences_desired):
            try:
                if the_text[-1] != "\n":
                    the_text = the_text + " "
            except IndexError:
                pass
            the_text = the_text + self._gen_sentence()
            if random.random() <= paragraph_break_probability or which_sentence == sentences_desired - 1:
                yield the_text.strip() + "\n"
                the_text = ""
        raise StopIteration

if __name__ == "__main__":
    if len(sys.argv) < 2: fname = '/home/patrick/Documents/programming/python_projects/AutoLovecraft/corpora/previous/All Edited Texts.3.pkl'
    else: fname = sys.argv[1]
    genny = TextGenerator(chainsfile = fname)
    print('\n'.join(genny._produce_text(sentences_desired=20)))
