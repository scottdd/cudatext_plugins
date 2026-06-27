"""Unicode to ASCII transliteration (vendored from anyascii, ISC license)."""

import os
from sys import intern
from zlib import MAX_WBITS, decompress

__version__ = '0.3.3'

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_data')
_blocks = {}


def anyascii(string):
    try:
        if string.isascii():
            return string
    except AttributeError:
        pass

    result = []
    for char in string:
        codepoint = ord(char)
        if codepoint <= 0x7F:
            result.append(char)
            continue

        blocknum = codepoint >> 8
        lo = codepoint & 0xFF
        try:
            block = _blocks[blocknum]
        except KeyError:
            try:
                with open(os.path.join(_DATA_DIR, '%03x' % blocknum), 'rb') as f:
                    b = f.read()
                s = decompress(b, -MAX_WBITS).decode('ascii')
                block = tuple(map(intern, s.split('\t')))
            except FileNotFoundError:
                block = ()
            _blocks[blocknum] = block

        if len(block) > lo:
            result.append(block[lo])

    return ''.join(result)