'''
TypePolicy.py - 
=================


.. warning::
        Documentation not done.

'''

import Policy


class TypePolicy(Policy.Policy):
    def __init__(self):
        super(TypePolicy, self).__init__(False)

    def work(self, belief):
        return raw_input('')
