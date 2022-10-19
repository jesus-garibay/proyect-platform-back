# -*- coding: utf-8 -*-
"""
Exception errors.
"""

__all__ = [
    "LendingException"
]


class LendingException(Exception):
    def __init__(self, message):
        super().__init__(message)
