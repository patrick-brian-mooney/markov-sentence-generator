#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""This module provides an object that creates poem-like text based on existing
poem-like text. That is, given a set of existing poems, this object creates
similar new "poems." It subclasses the generic text_generator object and serves
as an example of how to override its methods to produce new effects.

This module also provides a command-line interface to that object so that
"poems" can be generated in a terminal.
"""

import text_generator as tg


force_test = False


class poem_generator(tg.TextGenerator):
    """A subclass of TextGenerator for writing poem-like texts. Very much a work in
    progress, and will be for some time.

    This is also a demonstration of how to write a new text generator that
    subclasses TextGenerator, though at the moment it's not much of one.
    """

    def train(self, the_files, markov_length=3, character_tokens=True):
        """For now, we're just altering some defaults here"""
        tg.TextGenerator.train(self, the_files=the_files, markov_length=markov_length, character_tokens=character_tokens)

    def _printer(self, what, *pargs, **kwargs):
        """Override TextGenerator's printer method by just using standard built-in
        print().
        """
        print(what)


if __name__ == "__main__":
    if force_test:
        tg.main(generator_class=poem_generator, chars=True, count=8, input='/home/patrick/Documents/corpora/poetry/Laurence Hope: Last Poems.txt')
    else:
        tg.main(generator_class=poem_generator, **tg.process_command_line())
