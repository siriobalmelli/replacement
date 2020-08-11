#!/usr/bin/env python3
'''demo.py
python module exporting some dummy functions for use in testing replacement.py
(c) 2018 Sirio Balmelli
'''


def ret_kwargs(**kwargs):
    '''ret_kwargs()
    Return kwargs as a dictionary.
    '''
    return kwargs


def ret_a_dict(existing):
    '''ret_a_dict()
    append a key-value to 'existing' (if it exists)
    '''
    existing = existing or {}
    ret = {'secret': 42}
    ret.update(existing)
    return ret

def ret_a_stream():
    '''ret_a_stream()
    return a stream of text
    '''
    from io import StringIO
    ret = StringIO()
    ret.writelines(['1. hello\n', '2. world\n'])
    return ret

def ret_a_list(an_arg):
    '''ret_a_list()
    append a random number to 'existing' (if it exists)
    '''
    existing = an_arg or []
    return [42, "meaning"] + existing

class aClass:
    @staticmethod
    def invented_list():
        return ['hello', 'from', 'staticmethod']
