"""The fixture CV as a plain function, for helpers that are not fixtures."""

import copy

from conftest import _CV


def CV():
    return copy.deepcopy(_CV)
