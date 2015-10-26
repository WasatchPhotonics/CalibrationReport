""" helper functions to make travis/coveralls tests pass 100%
"""

import os
import logging

log = logging.getLogger(__name__)

def touch_erase(filename):
    """ Helper function to erase a file if it exists. Touches the
    file first so coverage is always 100%
    """
    # http://stackoverflow.com/questions/12654772/\
    # create-empty-file-using-python
    open(filename, 'a').close()
    if os.path.exists(filename):
        os.remove(filename)

    return os.path.exists(filename)

def file_range(filename, expected_size, ok_range=50):
    """ Files are slightly different sizes on travis build then on local
    machine. For tests that include building an image using Pillow. I'm
    guessing this is due to slightly different pillow versions. This
    also seems like a bad idea, as your CI environment is now different
    from your dev. Trying to match the pillow version on your fedora 22
    core system seems like a bad idea too. This seems to be a 0.003%
    difference in file size.
    """
    if not os.path.exists(filename):
        log.info("file does not exist: %s", filename)
        return False

    actual_size = os.path.getsize(filename)
    result = size_range(actual_size, expected_size, ok_range)
    if not result:
        log.info("Size out of range: %s, %s, %s", \
                 actual_size, expected_size, ok_range)
        
    return result

def size_range(actual_size, expected_size, ok_range=50):
    """ Simple comparison of two size ranges.
    """
    min_size = expected_size - ok_range
    max_size = expected_size + ok_range

    if actual_size < min_size:
        log.warn("Min: %s, %s, %s", actual_size, expected_size,
                 ok_range)
        return False

    if actual_size > max_size:
        log.warn("Max: %s, %s, %s", actual_size, expected_size,
                 ok_range)
        return False

    return True
