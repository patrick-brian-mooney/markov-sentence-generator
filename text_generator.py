#!/usr/bin/env python3.5
# -*- coding: utf-8 -*-
"""This is the actual code implementing Patrick Mooney's Markov chain-based
text generator, separated into a separate module so that it can easily be
compiled with Cython.

This module is licensed under the GNU GPL,either version 3, or (at your option)
any later version. See the files README.md and LICENSE.md for more details.
"""


import pickle
import re
import random
import time
import typing

from pathlib import Path

import text_handling as th          # https://github.com/patrick-brian-mooney/personal-library


cython = None

try:
    import cython
except Exception as errrr:
    print("Unable to import cython! The system said: {}".format(errrr))


__author__ = "Patrick Mooney, http://patrickbrianmooney.nfshost.com/~patrick/"
__version__ = "$v2.3 $"
__date__ = "$Date: 2020/05/05 23:16:00 $"
__copyright__ = "Copyright (c) 2015-20 Patrick Mooney"
__license__ = "GPL v3, or, at your option, any later version"


# logging-related stubs
verbosity_level = 1  # Bump above zero to get more verbose messages about processing and to skip the "are we running on a webserver?" check.

def log_it(what, log_level=1):
    """Handles logging to console, based on current verbosity_level. #FIXME: just use the stdlib logging module.
    """
    if log_level <= verbosity_level:
        print(what)


# Basic declarations about English-language text.
punct_with_space_after = r'.,\:!?;'
sentence_ending_punct = r'.!?'
punct_with_no_space_before = r'.,!?;—․-:/'
punct_with_no_space_after = r'—-/․'             # Note: that last character is U+2024, "one-dot leader".
word_punct = r"'’❲❳%°#․$"                       # Punctuation marks to be considered part of a word.
token_punct = r".,:\-!?;—/&…⸻"              # These punctuation marks also count as tokens.


# First, some utility functions.
def _is_cythonized() -> bool:
    if cython:
        return cython.compiled
    else:
        return False


def process_acronyms(text: str) -> str:
    """Takes TEXT and looks through it for acronyms. If it finds any, it takes each
    and converts their periods to one-dot leaders to make the Markov parser treat
    the acronym as a single word. Returns the modified string.

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


def to_hash_key(lst: list) -> tuple:
    """Tuples can be hashed; lists can't.  We need hashable values for dict keys.
    This looks like a hack (and it is, a little) but in practice it doesn't
    affect processing time too negatively.

    This is no longer used -- tuple() is now called directly to spare a function
    call -- but it's been allowed to stay here because of historical affection.
    """
    return tuple(lst)


def apply_defaults(defaultargs: dict, args: dict) -> dict:
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


def fix_caps(word: str) -> str:
    """This is Harry Schwartz's token comparison function, allowing words (other than
    "I") to be compared regardless of capitalization. I don't tend to use it, but
    if you want to, set the comparison_form attribute to point to it: something
    like

        genny.comparison_function = fix_caps

    should work. Note that this function is NEVER called BY DEFAULT; it's a utility
    function that's left in place in case anyone else ever wants to use it.
    """
    if word.isupper() and word != "I":      # I suspect this doesn't work the way Schwartz thinks it does, but haven't tested it.
        word = word.lower()                 # isupper() looks at whether the WHOLE STRING IS CAPITALIZED, not whether it HAS CAPS IN IT.
        # Ex: "LaTeX" => "Latex"            # So this example doesn't actually describe what's going on.
    elif word[0].isupper():
        word = th.capitalize(word.lower())  # I keep meaning to report this as a bug. #FIXME
        # Ex: "wOOt" -> "woot"
    else:
        word = word.lower()
    return word


class MarkovChainTextModel(object):
    """Chains representing a model of a text."""
    def __init__(self):
        """Instantiate a new, empty set of chains."""
        self.starts = None              # List of tokens allowed at the beginning of a sentence.
        self.markov_length = 0          # Length of the chains.
        self.mapping = None         # Dictionary representing the Markov chains.
        self.character_tokens = False   # True if the chains are characters, False if they are words.
        self.finalized = False

    def store_chains(self, filename: typing.Union[str, Path]):
        """Shove the relevant chain-based data into a dictionary, then pickle it and
        store it in the designated file.
        """
        chains_dictionary = { 'the_starts': self.starts,
                              'markov_length': self.markov_length,
                              'the_mapping': self.mapping,
                              'character_tokens': self.character_tokens }
        try:
            with open(filename, 'wb') as the_chains_file:
                the_pickler = pickle.Pickler(the_chains_file, protocol=-1)    # Use the most efficient protocol possible
                the_pickler.dump(chains_dictionary)
        except IOError as e:
            log_it("ERROR: Can't write chains to %s; the system said '%s'." % (filename, str(e)), 0)
        except pickle.PickleError as e:
            log_it("ERROR: Can't write chains to %s because a pickling error occurred; the system said '%s'." % (filename, str(e)), 0)

    def read_chains(self, filename: typing.Union[str, Path]):
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
        self.starts = chains_dictionary['the_starts']
        self.mapping = chains_dictionary['the_mapping']
        self.character_tokens = chains_dictionary['character_tokens']
        self.finalized = True


class TextGenerator(object):
    """A general-purpose text generator. To use it, instantiate it, train it, and
    then have it generate text.
    """
    def __init__(self, name: typing.Optional[str]=None, training_texts: typing.Optional[list]=None, **kwargs):
        """Create a new instance. NAME is entirely optional, and is mentioned for
        convenience (if it exists) any time a string representation is generated.
        If TRAINING_TEXTS is not None, it should be a *list* of one or more
        filenames on which the generator will be immediately trained. If you want
        to specify parameters to train() other than just a list of files (e.g., if
        you want to pass a markov_length parameter so that the chains have a length
        greater than one), you can pass them as keyword arguments here, at the end
        of the parameter list; anything not collected by the keyword arguments
        explicitly specified in this function's definition will be passed on to
        train(). (Or, you can instead call train() separately after object
        creation, if you wish.)
        """
        self.name = name                                # NAME is totally optional and entirely for your benefit.
        self.chains = MarkovChainTextModel()            # Markov chain-based representation of the text(s) used to train this generator.
        self.allow_single_character_sentences = False   # Is this model allowed to produce one-character sentences?

        # This next is the default list of substitutions that happen after text is produced.
        # List of lists. each sublist:[search_regex, replace_regex]. Subs performed in order specified.
        if training_texts:
            self.train(training_texts, **kwargs)

    final_substitutions = [
        ['--', '—'],
        ['\.\.\.', '…'],
        ['․', '.'],  # replace one-dot leader with period
        ['\.\.', '.'],
        [" ' ", ''],
        ['――', '―'],  # Two horizontal bars to one horizontal bar
        ['―-', '―'],  # Horizontal bar-hyphen to single horizontal bar
        [':—', ': '],
        ["\n' ", '\n'],  # newline--single quote--space
        ["<p>'", '<p>'],
        ["<p> ", '<p>'],  # <p>-space to <p> (without space)
        ["<p></p>", ''],  # <p></p> to nothing
        ['- ', '-'],  # hyphen-space to hyphen
        ['—-', '—'],  # em dash-hyphen to em dash
        ['——', '—'],  # two em dashes to one em dash
        ['([0-9]),\s([0-9])', r'\1,\2'],  # Remove spaces after commas when commas are between numbers.
        ['([0-9]):\s([0-9])', r'\1:\2'],  # Remove spaces after colons when colons are between numbers.
        ['…—', '… —'],  # put space in between ellipsis-em dash, if they occur together.
    ]

    def __str__(self):
        if self.is_trained():
            if self.name:
                return '< class %s, named "%s", with Markov length %d >' % (self.__class__, self.name, self.chains.markov_length)
            else:
                return '< class %s (unnamed instance), with Markov length %d >' % (self.__class__, self.chains.markov_length)
        else:
            if self.name:
                return '< class %s, named "%s", UNTRAINED >' % (self.__class__, self.name)
            else:
                return '< class %s (unnamed instance), UNTRAINED >' % self.__class__

    @staticmethod
    def comparison_form(word: str) -> str:
        """This function is called to normalize words for the purpose of storing
        them in the list of Markov chains, and for looking at previous words when
        deciding what the next word in the sequence should be. By default, this
        function performs no processing at all; override it if any preprocessing
        should be done for comparison purposes -- for instance, if case needs to be
        normalized.
        """
        return word

    def add_final_substitution(self, substitution: str, position: int=-1):
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

    def remove_final_substitution(self, substitution: str):
        """Remove SUBSTITUTION from the list of final substitutions performed after text
        is generated. You must pass in *exactly* the substitution you want to remove.
        If you try to remove something that's not there, this routine will let the error
        raised by the list (which is always[?] ValueError) propagate -- trap it if you
        need to.
        """
        assert isinstance(substitution, (list, tuple)), "ERROR: the substitution you pass in must be a list or tuple."
        assert len(substitution) == 2, "ERROR: the substitution you pass in must be two items long."
        self.final_substitutions.remove(substitution)

    def get_final_substitutions(self) -> typing.List[str]:          #FIXME: check annotation
        """Returns the list of final substitutions that are performed by the text generator
        before returning the text. Just a quick index into a variable in the object
        namespace.
        """
        return self.final_substitutions

    def set_final_substitutions(self, substitutions: typing.List[str]):     # FIXME: check annotation
        """Set the list of final substitutions that are performed on generated text before
        it's returned. SUBSTITUTIONS must be a list of two-item lists, of the form
        [regex to search for, replacement], as in the default list in the __init__()
        method for the class.
        """
        for sublist in substitutions:       # Do some basic error-checking
            assert isinstance(sublist, (list, tuple)), "ERROR: substitution %s is not a list or tuple." % sublist
            assert len(sublist) == 2, "ERROR: substitution %s is not two items long." % sublist
        self.final_substitutions = substitutions

    def addItemToTempMapping(self, history: typing.List[str],             #FIXME: check annotations
                             word: str,
                             weight: typing.Union[float, int]=1.0) -> None:
        """Self-explanatory -- adds "word" to the "the_temp_mapping" dict under "history".
        the_temp_mapping (and the_mapping) both match each word to a list of possible next
        words.

        WEIGHT is a real number (by default, 1.0) indicating how much 'weight' to add to
        this mapping in the temporary mapping. Items that are weighted more heavily will
        of course be more likely to pop back out.

        Given history = ["the", "rain", "in"] and word = "Spain", we add "Spain" to
        the entries for ["the", "rain", "in"], ["rain", "in"], and ["in"].
        """
        while len(history) > 0:
            first = tuple(history)
            if first in self.the_temp_mapping:
                if word in self.the_temp_mapping[first]:
                    self.the_temp_mapping[first][word] += weight
                else:
                    self.the_temp_mapping[first][word] = weight
            else:
                self.the_temp_mapping[first] = dict()
                self.the_temp_mapping[first][word] = weight
            history = history[1:]

    def next(self, prevList: typing.List,                           #FIXME: check annotations
             the_mapping: typing.Dict) -> str:
        """Returns the next word in the sentence (chosen randomly),
        given the previous ones.
        """
        prevList = [ self.comparison_form(p) for p in prevList ]        # Use the canonical comparison form
        total = 0.0
        ret = ""
        index = random.random()
        # Shorten prevList until it's in the_mapping
        try:
            while tuple(prevList) not in the_mapping:
                prevList.pop(0)         # Just drop the earliest list element & try again if the list isn't in the_mapping
        except IndexError:  # If we somehow wind up with an empty list (shouldn't happen), then just end the sentence;
            ret = "."    # this will force the generator to start a new one.
        else:               # Otherwise, get a random word from the_mapping, given prevList, if prevList isn't empty
            for k, v in the_mapping[tuple(prevList)].items():
                total += v
                if total >= index and ret == "":
                    ret = k
                    break
        return ret

    def _build_mapping(self, token_list: typing.List[str],          #FIXME: check annotations
                       markov_length: int,
                       character_tokens: bool=False,
                       learn_starts: bool=True,
                       weight: typing.Union[float, int]=1.0) -> None:
        """Add the data in TOKEN_LIST to the temporary mapping data that is being built
        as the model is trained. If CHARACTER_TOKENS is True, sets the corresponding
        flag on the chains (and the chains that are passed in should also be letters,
        not words: this is not checked, but getting it wrong may result in weird
        behavior later on). MARKOV_LENGTH is of course the length of the Markov chains
        being generated. If LEARN_STARTS in True (the default), the first words of
        sentences in TOKEN_LIST are also added to the .starts attribute of the chains.
        This is normally desirable, and there has to be SOMETHING in .starts for a
        set of chains to be able to produce text; but there may be texts (such as texts
        containing partial sentences, say) that we want to train a generator on but that
        consist of incomplete sentences; setting LEARN_STARTS to False for those texts
        allows them to pad the existing chains without worrying that weird uncapitalized
        and grammatically weird sentences will result because of this fact. WEIGHT is
        the relative weighting to give to these tokens in the mapping; this will be
        normalized later when _finalize_mappings is called.

        This function does not finalize the mappings by normalizing the frequency
        counts; _finalize_mapping needs to be called for that.
        """
        try:
            _ = self.the_temp_mapping
        except AttributeError:
            self.the_temp_mapping = dict()
        if (not hasattr(self.chains, 'starts')) or not (self.chains.starts):
            self.chains.starts = list()

        self.chains.markov_length = markov_length
        self.chains.character_tokens = character_tokens
        if token_list[0] not in self.chains.starts:
            self.chains.starts.append(token_list[0])
        for i in range(1, len(token_list) - 1):
            if i <= markov_length:
                history = token_list[: i + 1]
            else:
                history = token_list[i - markov_length + 1 : i + 1]
            follow = token_list[i + 1]
            # if the last elt was a sentence-ending punctuation, add the next word to the start list
            if learn_starts:
                if history[-1] in sentence_ending_punct and follow not in punct_with_space_after:
                    if follow not in self.chains.starts:
                        self.chains.starts.append(follow)
            self.addItemToTempMapping(history, follow, weight=weight)

    def _finalize_mapping(self):
        """Finalize the mapping in SELF by normalizing probability frequencies of
        occurrences. This must be done once, after the model has been trained on
        all texts, but not more than once. The higher-level train() method calls it and
        is a good choice if we're passing in one set of texts that has one set of
        parameters that get set all at once. For fiddlier training processes that don't
        happen atomically, it should be called manually once everything is done.
        """
        # First, check the invariants
        assert hasattr(self, 'the_temp_mapping'), "ERROR! The text generator has not been trained!"
        assert self.the_temp_mapping, "ERROR! Training for the text generator has not begun!"
        assert hasattr(self.chains, 'starts'), "ERROR! The text generator's training did not result in any sentence beginnings!"
        assert self.chains.starts, "ERROR! The text generator's training did not result in any sentence beginnings!"

        # Next, restrict the possible range of STARTS if we're using single-chracter chains.
        if self.chains.character_tokens:
            self.chains.starts = [c for c in self.chains.starts if c.isupper()]

        # Then, normalize the frequencies and install the new dictionary in the object's mappings.
        the_mapping = dict()
        for first, followset in self.the_temp_mapping.items():
            total = sum(followset.values())
            the_mapping[first] = dict([(k, v / total) for k, v in followset.items()])   # Here's the normalizing step.
        self.chains.mapping = the_mapping

        # Clean up and mark finalized.
        del self.the_temp_mapping
        self.chains.finalized = True

    @staticmethod
    def _tokenize_string(the_string: str) -> typing.List[str]:
        """Split a string into tokens, which more or less correspond to words. More aware
        than a naive str.split() because it takes punctuation into account to some
        extent.
        """
        return re.findall(r"[\w%s]+|[%s]" % (word_punct, token_punct), the_string)

    def _token_list(self, the_string: str,
                    character_tokens: bool=False) -> typing.List[str]:
        """Converts a string into a set of tokens so that the text generator can
        process, and therefore be trained by, it.
        """
        if character_tokens:
            tokens = list(the_string)
        else:
            tokens = self._tokenize_string(the_string)
        return [self.comparison_form(w) for w in tokens]

    def is_trained(self) -> bool:
        """Detect whether this model is trained or not."""
        return all([self.chains.finalized, self.chains.starts, self.chains.mapping, self.chains.markov_length])

    def _train_from_text(self, the_text: str,
                         markov_length: int=1,
                         character_tokens: bool=False,
                         weight: typing.Union[float, int]=1.0,
                         learn_starts: bool=True) -> None:
        """Train the model by getting it to analyze a text passed in. Note that THE_TEXT is
        a single string here. MARKOV_LENGTH is, of course, the length of the Markov
        chains to generate; CHARACTER_TOKENS indicates whether tokens are single
        characters (if it is True) or whole words (if it is False). WEIGHT is the
        relative numerical weighting to give to this piece of text. LEARN_STARTS
        toggles whether the beginnings of sentences are added to the generator's
        .starts list, which is generally desirable but needs to be turned off in some
        situations.
        """
        assert the_text, "ERROR! blank text was passed to _train_from_text()!"
        self._build_mapping(self._token_list(the_text, character_tokens=character_tokens),
                            markov_length=markov_length, character_tokens=character_tokens,
                            weight=weight, learn_starts=learn_starts)

    def train(self, the_files: typing.Union[str, bytes, Path, typing.List[typing.Union[str, bytes, Path]]],
              markov_length: int=1,
              character_tokens: bool=False) -> None:
        """Train the model from a text file, or a list of text files, supplied as THE_FILES.
        This routine is the easiest way to train a generator all at once on a single
        file or set of files that all have the same training parameters. Fiddlier
        training process will need to call _train_from_text() manually at least once,
        then _finalize_mapping when all of the mappings have been created.
        """
        if isinstance(the_files, (str, bytes, Path)):
            the_files = [ the_files ]
        assert isinstance(the_files, (list, tuple)), "ERROR: you cannot pass an object of type %s to %s.train" % (type(the_files), self)
        assert len(the_files) > 0, "ERROR: empty file list passed to %s.train()" % self
        the_text = ""
        for which_file in the_files:
            with open(which_file) as the_file:
                the_text = the_text + '\n' + the_file.read()
        self._train_from_text(the_text=the_text, markov_length=markov_length, character_tokens=character_tokens)
        self._finalize_mapping()

    def _gen_sentence(self) -> str:
        """Build a sentence, starting with a random 'starting word.' Returns a string,
        which is the generated sentence.
        """
        assert self.is_trained(), "ERROR: the model %s needs to be trained before it can generate text!" % self
        log_it("      _gen_sentence() called.", 4)
        log_it("        markov_length = %d." % self.chains.markov_length, 5)
        log_it("        the_mapping = %s." % self.chains.mapping, 5)
        log_it("        starts = %s." % self.chains.starts, 5)
        log_it("        allow_single_character_sentences = %s." % self.allow_single_character_sentences, 5)
        curr = random.choice(self.chains.starts)
        sent = curr
        prevList = [curr]
        # Keep adding words until we hit a period, exclamation point, or question mark
        while curr not in sentence_ending_punct:
            curr = self.next(prevList, self.chains.mapping)
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

    def _produce_text(self, sentences_desired: int=1,
                      paragraph_break_probability: float=0.25) -> str:
        """Actually generate some text. This is a generator function that produces (yields)
        one paragraph at a time. If you just need all the text at once, you might want
        to use the convenience wrapper gen_text() instead.
        """
        log_it("_produce_text() called.", 4)
        log_it("  Markov length is %d; requesting %d sentences." % (self.chains.markov_length, sentences_desired), 4)
        log_it("  Legitimate starts: %s" % self.chains.starts, 5)
        log_it("  Probability data: %s" % self.chains.mapping, 5)
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
                try:
                    yield the_text.strip() + "\n"
                except RuntimeError:                    # Conforms to Python 3.7 changes in behavior. Sigh.
                    return
                the_text = ""

    def gen_text(self, sentences_desired: int=1,
                 paragraph_break_probability: float=0.25) -> str:
        """Generate the full amount of text required. This is just a convenience wrapper
        for _produce_text().
        """
        return '\n'.join(self._produce_text(sentences_desired, paragraph_break_probability))

    def gen_html_frag(self, sentences_desired: int=1,
                      paragraph_break_probability: float=0.25):
        """Produce the same text that _produce_text would, but wrapped in HTML <p></p> tags."""
        log_it("We're generating an HTML fragment.", 3)
        the_text = self._produce_text(sentences_desired, paragraph_break_probability)
        return '\n\n'.join(['<p>%s</p>' % p.strip() for p in the_text])

    def _printer(self, what: str,
                 columns: int=-1):
        """Print WHAT in an appropriate way, wrapping to the specified number of
        COLUMNS. If COLUMNS is -1, take a whack at guessing what it should be. If
        COLUMNS is zero, do no wrapping at all.
        """
        if columns == 0:  # Wrapping is totally disabled. Print exactly as generated.
            log_it("INFO: COLUMNS is zero; not wrapping text at all", 3)
            print(what)
        else:
            if columns == -1:  # Wrap to best guess for terminal width
                log_it("INFO: COLUMNS is -1; wrapping text to best-guess column width", 3)
                padding = 0
            else:  # Wrap to specified width (unless current terminal width is odd, in which case we're off by 1/2. Oh well.)
                padding = max((th.terminal_width() - columns) // 2, 0)
                log_it("INFO: COLUMNS is %s; padding text with %s spaces on each side" % (columns, padding), 3)
                log_it("NOTE: terminal width is %s" % th.terminal_width(), 3)
            what = th.multi_replace(what, [['\n\n', '\n'], ])       # Last chance to postprocess text is right here
            for the_paragraph in what.split('\n'):
                if the_paragraph:                   # Skip any empty paragraphs that may pop up
                    th.print_indented(the_paragraph, each_side=padding)
                    print()

    def print_text(self, sentences_desired: int,
                   paragraph_break_probability: float=0.25,
                   pause: float=0,
                   columns: int=-1):
        """Prints generated text directly to stdout."""
        for t in self._produce_text(sentences_desired, paragraph_break_probability):
            time_now = time.time()
            self._printer(t, columns=columns)
            time.sleep(max(pause - (time.time() - time_now), 0))    # Pause until it's time for a new paragraph.


if __name__ == "__main__":
    gen = TextGenerator()
    gen.train(['/lovecraft/corpora/previous/The Alchemist.txt'])
    gen.print_text(25)

