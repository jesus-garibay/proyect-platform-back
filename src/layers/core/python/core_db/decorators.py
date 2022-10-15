# -*- coding: utf-8 -*-
"""
Helper functions for working with database.
"""

import functools

import peewee


def transaction_for_test(database=None):
    """Decorator for test functions that will use a transaction.
    Create a transaction which wraps your tests in such a way that when the unit test ends, the database
    remains in the initial state when the test was not yet executed

    Parameters
    ----------
    database : peewee.Database
        a connection to database.

    Returns
    -------
    function

    Examples
    --------
    >>> from core_db.decorators import transaction_for_test
    >>> from core_db.base_model import database
    >>> @transaction_for_test(database=database)
    ... def test_function():
    ...     pass
    """

    def decorator(func):
        if not isinstance(database, peewee.PostgresqlDatabase):
            raise ValueError("Error")
        if database.is_closed():
            database.connect()

        @functools.wraps(func)
        def decorator_nest(self, *args, **kwargs):
            with database.transaction() as t:
                result = func(self, *args, **kwargs)
                t.rollback()
                return result

        database.close()
        return decorator_nest

    return decorator
