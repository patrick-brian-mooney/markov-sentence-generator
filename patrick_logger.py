#!/usr/bin/env python3
"""patrick_logger.py is a simple multi-verbosity-level logger for when
the standard library module is way more than needed. Several of my
scripts depend on this module.

GPL v3+ at your option. No guarantees or representations of fitness
or warranties apply. This is free software; you're getting more than
what you paid for. Nevertheless, I'd love to hear suggestions or
feedback if anything occurs to you.

http://patrickbrianmooney.nfshost.com/~patrick/

v1, 7 October 2015. 
""" 

# Can set the starting level above zero explicitly when debugging, esp. when debugging command-line options
verbosity_level = 0

def log_it(message,minimum_level=1):
    """Add a message to the log if verbosity_level is at least minimum_level.
    Currently, the log goes to standard output.
    """
    if verbosity_level >= 4: # set verbosity to at least 4 to get this message output in the debug log
        print("\nDEBUGGING: function log_it() called")
    if verbosity_level >= minimum_level:
        print(message)

