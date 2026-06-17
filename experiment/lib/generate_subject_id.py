from __future__ import print_function

from numpy.random import RandomState

rng = RandomState()

abc = "abcdefghijklmnopqrstuvwxyz"

print("".join(rng.choice(list(abc), 2)))
