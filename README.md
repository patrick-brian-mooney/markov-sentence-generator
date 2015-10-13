Markov Sentence Generator
=========================

This program generates a sentence's worth of "real-looking" text using a Markov model and sample textual training input.  Given some sample text from which to build a model, the program prints out a sentence based on a Markov chain.  Use it thus:

`$ ./sentence-generator.py  filename  [chain length]`

where `filename` is a file containing some training text for the sentence to imitate (one of Project Gutenberg's books fits the bill nicely) and `chain length` optionally represents the number of words taken into account when choosing the next word.  Chain length defaults to 1 (which is fastest), but increasing this may generate more realistic text, albeit slightly more slowly.  Depending on the text, increasing the chain length past 6 or 7 words probably won't do much good -- at that point you're usually plucking out whole sentences anyway, so using a Markov model is kind of redundant.

This script is Patrick Mooney's fork of [Harry R. Schwartz's Markov Sentence Generator](https://github.com/hrs/markov-sentence-generator), modified for my automated text blog *Ulysses Redux*.  HRS did the hard work here; my changes reflect adaptations to the needs of that particular project (and an opportunity to learn a bit about Python and Markov chain-based text processing.) If you're looking for a generalized Markov chain implementation, Schwartz's project is more likely to be what you need, though if you want to develop this, it, like Schwartz's implementation, is licensed under the GPL, either version 3 or (at your option) any later option.

A copy of [version 3 of the GPL](http://www.gnu.org/licenses/gpl-3.0.en.html) is included as the file LICENSE.md; a listing of changes is included as the file HISTORY.md.