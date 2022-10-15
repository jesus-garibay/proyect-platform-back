# -*- coding: utf-8 -*-
"""
Helper functions for working with Python.
"""

import datetime
import json
import os
import uuid
from decimal import Decimal
from typing import Union

import pytz
from aws_lambda_powertools import Logger

__all__ = [
    "get_logger",
    "get_mty_datetime",
    "cast_default",
    "cast_date",
    "cast_number",
    "compare_iterables",
    "dict_strip_nulls",
    "dict_keys_to_lower",
    "sort_dict_by_keys",
    "get_uniques_in_lists",
    "get_split_names",
    "cast_python_default",
    "bytes_to",
    "update_dict",
    "get_tmp_path",
    "get_timezone_datetime",
    "calculate_last_date",
    "calculate_interest",
    "calculate_administrative_expense",
    "calculate_iva",
    "generate_requester"
]

LOG_LEVELS = {"1": "DEBUG", "2": "INFO", "3": "WARNING", "4": "ERROR", "5": "CRITICAL"}


def get_logger(name=None):
    """
    Returns a logger object.

    Parameters
    ----------
    name : str

    Returns
    -------
    logger : Logger

    Examples
    --------
    >>> from core_utils.utils import get_logger
    >>> logger = get_logger("my_logger")

    """
    level_log = LOG_LEVELS.get(os.environ.get("LOG_LEVEL", "2"))
    return Logger(
        service=name,
        level=level_log,
        log_record_order=["level", "message"],
        location=None,
        sampling_rate=None,
    )


def get_mty_datetime():
    """
    Returns a datetime object with the current time in Mexico City "America/Monterrey" timezone

    Returns
    -------
    datetime.datetime object with the current time in Mexico City "America/Monterrey" timezone.

    Examples
    --------
    >>> from core_utils.utils import get_mty_datetime
    >>> mty_datetime = get_mty_datetime()

    """
    mty = pytz.timezone("America/Monterrey")
    return datetime.datetime.now(tz=mty)


def cast_default(o):
    """
    Cast data to default data for json serialization.

    Parameters
    ----------
    o : Any

    Returns
    -------
    Any object with the default data type for json serialization.

    Examples
    --------
    >>> from core_utils.utils import cast_default
    >>> cast_default(Decimal(1.1))

    """
    if isinstance(o, (datetime.date, datetime.time)):
        o = cast_date(o)
    if isinstance(o, Decimal):
        o = cast_number(o)
    return o


def cast_date(element: Union[datetime.date, datetime.time]):
    """
    Cast a datetime.date or datetime.time object to iso-format string.

    Parameters
    ----------
    element: datetime.date or datetime.time object

    Returns
    -------
    str: iso-format string

    Examples
    --------
    >>> from core_utils.utils import cast_date
    >>> cast_date(datetime.date(2020, 1, 1))

    """
    if isinstance(element, (datetime.date, datetime.time)):
        element_ = element.isoformat()
        return element_


def cast_number(number: Union[str, Decimal]) -> Union[int, float]:
    """
    Cast a string or Decimal object to int or float.

    Parameters
    ----------
    number : str or Decimal

    Returns
    -------
    int or float

    Examples
    --------
    >>> from core_utils.utils import cast_number
    >>> cast_number(Decimal(1.1))

    """
    if isinstance(number, str):
        if number.isnumeric():
            return int(number)
        else:
            try:
                return float(number)
            except ValueError:
                try:
                    return float(number.replace(",", ""))
                except ValueError:
                    raise ValueError("The value not is int o float")
    elif isinstance(number, Decimal):
        return cast_number(str(number))
    elif isinstance(number, (float, int)):
        return number


def compare_iterables(keys, this):
    """
    Compare two iterables.
    Check that all the elements of the (list, tuple or dict) passed as keys exist in
    the (list, tuple or dict) passed as "this"

    Parameters
    ----------
    keys : list, tuple or dict
    this : list, tuple or dict

    Returns
    -------
    bool: True if all the elements of the (list, tuple or dict) passed as keys exist in
    the (list, tuple or dict) passed as "this"

    Examples
    --------
    >>> from core_utils.utils import compare_iterables
    >>> compare_iterables(["a", "b"], ["a", "b", "c"])
    """
    return (
        all([key in this for key in keys])
        if isinstance(keys, (list, dict)) and isinstance(this, (list, dict))
        else False
    )


def dict_strip_nulls(d):
    """
    Remove null values from a dictionary.

    Parameters
    ----------
    d : dict

    Returns
    -------
    dict: dict without null values

    Examples
    --------
    >>> from core_utils.utils import dict_strip_nulls
    >>> dict_strip_nulls({"a": 1, "b": None})

    """
    return {k: v for k, v in d.items() if v is not None} if type(d) == dict else None


def dict_keys_to_lower(d):
    """
    Convert all keys of a dictionary to lowercase.

    Parameters
    ----------
    d : dict

    Returns
    -------
    dict: dict with all keys in lowercase

    Examples
    --------
    >>> from core_utils.utils import dict_keys_to_lower
    >>> dict_keys_to_lower({"a": 1, "B": 2})

    """
    return {k.lower(): v for k, v in d.items()} if type(d) == dict else None


def bytes_to(bytes_, to=0, bsize=1024):
    """
    Convert bytes to MB, GB, TB, or PB.

    Parameters
    ----------
    bytes_  : int
        A number representing the size of a file in bytes
    to     : int
        index of the metric you want to use:
            1: 'Kb',
            2: 'Mb',
            3: 'Gb',
            4: 'Tb',
            5: 'Pb',
            6: 'Eb'
    bsize : int
        size of a block

    Returns
    -------
    int: bytes converted to MB, GB, TB, or PB
    the value converted to the desired units in case of not defining the value for the
        argument "to" will automatically be converted to the corresponding unit

    Examples
    --------
    >>> from core_utils.utils import bytes_to
    >>> bytes_to(1024)

    """
    a = {0: "", 1: "K", 2: "M", 3: "G", 4: "T", 5: "P", 6: "E"}
    r = float(bytes_)
    for _ in range(to):
        r = r / bsize
    if r >= 1000:
        to += 1
        return bytes_to(bytes_, to)
    r = f"{str(r)[:str(r).index('.') + 2]}{a[to]}B"
    return r


def sort_dict_by_keys(data, keys, reverse=False):
    """
    Sort a dictionary by keys.

    Parameters
    ----------
    data : dict
    keys : list
    reverse : bool

    Returns
    -------
    dict: sorted dictionary by keys.

    Examples
    --------
    >>> from core_utils.utils import sort_dict_by_keys
    >>> sort_dict_by_keys({"a": 1, "b": 2}, ["a", "b"])

    """
    return sorted(data, key=lambda x: [x[k] for k in keys], reverse=reverse)


def cast_python_default(data):
    """
    Cast python default values.

    Parameters
    ----------
    data : dict

    Returns
    -------
    dict: casted python default values.

    Examples
    --------
    >>> from core_utils.utils import cast_python_default
    >>> cast_python_default({"a": 1, "b": Decimal(1)})

    """
    return json.loads(json.dumps(data, default=cast_default, ensure_ascii=False))


def get_uniques_in_lists(iter_a, iter_b):
    """
    Get uniques in two lists.

    Parameters
    ----------
    iter_a : list
    iter_b : list

    Returns
    -------
    list: uniques in two lists.

    Examples
    --------
    >>> from core_utils.utils import get_uniques_in_lists
    >>> get_uniques_in_lists([1, 2, 3], [2, 3, 4])

    """
    return list(filter(lambda x: x not in iter_a, iter_b)) + list(
        filter(lambda x: x not in iter_b, iter_a)
    )


def get_split_names(full_name):
    """
    Get split names.

    Parameters
    ----------
    full_name : str

    Returns
    -------
    tuple: split names.

    Examples
    --------
    >>> from core_utils.utils import get_split_names
    >>> get_split_names("name1 name2 last_name second_name")

    """
    first_name, second_name = "", ""
    words = full_name.split()
    # List where the full_names_parts of the last name are saved.
    full_names_parts = []
    # full_names_parts of last names and compound names.
    special_words = [
        "da",
        "de",
        "di",
        "do",
        "del",
        "la",
        "las",
        "le",
        "los",
        "mac",
        "mc",
        "van",
        "von",
        "y",
        "i",
        "san",
        "santa",
    ]
    aux = ""
    for word in words:
        if word.lower() in special_words:
            aux += word + " "
        else:
            full_names_parts.append(aux + word)
            aux = ""
    num_full_names_parts = len(full_names_parts)
    if num_full_names_parts == 1:
        first_name = full_names_parts[0]
    else:
        first_name = full_names_parts[0]
        full_names_parts.remove(first_name)
        for i, name in enumerate(full_names_parts):
            second_name += full_names_parts[i]
            if i + 1 != len(full_names_parts):
                second_name += " "
    return first_name, second_name


def update_dict(d, u):
    """
    Update dictionary.

    Parameters
    ----------
    d : dict
    u : dict

    Returns
    -------
    dict: updated dictionary.

    Examples
    --------
    >>> from core_utils.utils import update_dict
    >>> update_dict({"a": 1, "b": 2}, {"a": 2})

    """
    d.update(u)
    return d


def get_tmp_path():
    """
    Returns path to save temporary files.
    """
    return "/tmp" if os.name == "posix" else "."


def get_timezone_datetime(timezone):
    """
    Get split names.

    Parameters
    ----------
    timezone : str

    Returns
    -------
    datetime.datetime object with the current time in TimeZone prameter.

    Examples
    --------
    >>> from core_utils.utils import get_timezone_datetime
    >>> tz_datetime = get_timezone_datetime()

    """
    tz = pytz.timezone(timezone)
    return datetime.datetime.now(tz=tz)


def calculate_last_date(days):
    date = str(datetime.datetime.now())
    date_start = datetime.datetime.strptime(date[0:10], '%Y-%m-%d')
    date_end = date_start + datetime.timedelta(days=days)
    return str(date_end)


def calculate_interest(ordinary_annual_interest, days, capital):
    return ((Decimal(ordinary_annual_interest) / 365) * int(days) * capital) / 100


def calculate_administrative_expense(administrative_expense, capital):
    return (administrative_expense * capital) / 100


def calculate_iva(vat, interest, total_administrative):
    interest_with_total_administrative = interest + total_administrative
    return (vat * interest_with_total_administrative) / 100


def generate_requester():
    """
    generate a RequestId and IdepontencyKey for mambu requests.

    Parameters
    ----------

    Returns
    -------
    dict.

    Examples
    --------
    >>> from core_utils.utils import generate_requester
    >>> requester = generate_requester()

    """
    return {
        "RequestId": int(round(datetime.datetime.now().timestamp())),
        "IdempotencyKey": str(uuid.uuid4())
    }
