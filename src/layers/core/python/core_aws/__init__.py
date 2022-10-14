# -*- coding: utf-8 -*-
from core_utils import (
    load_environment_variables,
)

load_environment_variables()
__all__ = [
    "cognito",
    "lambdas",
    "s3",
    "ssm",
    "dynamo",
    "sqs"
]
