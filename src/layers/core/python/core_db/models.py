# -*- coding: utf-8 -*-
from core_db.base_model import BaseModel
from peewee import (
    SQL,
    BigAutoField,
    BooleanField,
    CharField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    IntegerField,
    TextField,
    UUIDField,
    DoubleField,
)

SCHEMA = "lending"

__all__ = [
]

UUID4 = "DEFAULT uuid_generate_v4()"
NOW = "DEFAULT now()"

