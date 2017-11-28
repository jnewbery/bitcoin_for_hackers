from binascii import hexlify, unhexlify

import hashlib

def bytes_to_str(b, encoding='ascii'):
    '''Returns a string version of the bytes'''
    return b.decode(encoding)

def str_to_bytes(s, encoding='ascii'):
    '''Returns a bytes version of the string'''
    return s.encode(encoding)

def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()

def double_sha256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()

def flip_endian(h):
    '''flip_endian takes a hex string and flips the endianness
    Returns a hexadecimal string
    '''
    return hexlify(unhexlify(h)[::-1]).decode('ascii')

def little_endian_to_int(b):
    '''little_endian_to_int takes byte sequence as a little-endian number.
    Returns an integer'''
    return int.from_bytes(b, 'little')

def int_to_little_endian(n, length):
    '''endian_to_little_endian takes an integer and returns the little-endian
    byte sequence of length'''
    return n.to_bytes(length, byteorder='little')
