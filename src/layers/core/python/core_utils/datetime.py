# -*- coding: utf-8 -*-
"""
Helper functions for working with datetime objects.
"""

import calendar
import datetime

__all__ = [
    "add_months",
    "get_name_month_in_spanish"
]


def add_months(source_date, months):
    """
    Add months to a date.

    Parameters
    ----------
    source_date : datetime.date
    months : int

    Returns
    -------
    datetime.date : date with added months

    Examples
    --------
    >>> from core_utils.datetime import add_months
    >>> add_months(datetime.date(2020, 1, 1), 1)

    """
    month = source_date.month - 1 + months
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    return datetime.date(year, month, day)


def get_name_month_in_spanish(month_id, capitalize=False, upper=False):
    """
    Get the name of a month in spanish.

    Parameters
    ----------
    month_id : int (1-12)
    capitalize : bool
    upper : bool

    Returns
    -------
    str : name of the month in spanish (capitalized or upper case or not).

    Examples
    --------
    >>> from core_utils.datetime import get_name_month_in_spanish
    >>> get_name_month_in_spanish(1)

    """
    if 0 >= month_id > 12:
        return None
    month_id -= 1
    spanish_name = (
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )
    month = spanish_name[month_id]
    if capitalize:
        return month.capitalize()
    elif upper:
        return month.upper()
    else:
        return month


class DateRange:
    """
    Class to manage a range of dates.
    """

    def __init__(self, start, end=None):
        """

        Parameters
        ----------
        start : str or datetime.date
        end : str or datetime.date
        """
        self.start = self.__parse_date(start)
        if not end:
            end = datetime.datetime.now().date()
        self.end = self.__parse_date(end)
        self.date = None

    @staticmethod
    def __parse_date(date):
        """
        Parse a date.

        Parameters
        ----------
        date : str or datetime.date

        Returns
        -------
        datetime.date

        """
        if isinstance(date, str):
            return datetime.datetime.strptime(date, "%Y-%m-%d").date()
        elif isinstance(date, datetime.date):
            return date
        else:
            raise ValueError(
                f"expected a date or str value but get a {type(date)} value"
            )

    def __iter__(self):
        """
        Iterate over the dates in the range.

        Returns
        -------
        self : DateRange

        """
        return self

    def __str__(self):
        """
        Return the range as a string.

        Returns
        -------
        str

        """
        return str(self.date if self.date else self.start)

    def __next__(self):
        """
        Return the next date in the range.

        Returns
        -------
        datetime.date
        """
        if not self.date:
            self.date = self.start
            return self.date
        if self.date < self.end:
            self.date += datetime.timedelta(days=1)
            return self.date
        else:
            raise StopIteration
