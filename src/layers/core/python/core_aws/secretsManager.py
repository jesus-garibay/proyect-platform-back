# -*- coding: utf-8 -*-
import json
import logging

import boto3
from botocore import exceptions
from core_utils.environment import (
    ENVIRONMENT,
)

SECRET_CLIENT = boto3.client("secretsmanager")

__all__ = ["get_secret"]

LOGGER = logging.getLogger("layer-ssm")


def get_secret(secret_name, use_environ=False, is_dict=True):
    """
    Get a parameter from Secret Manager service on aws.

    Parameters
    ----------
    secret_name : str
        The name of the parameter to get.
    use_environ : bool
        If True, the environment variable will be used to get the parameter.
    is_dict : bool

    Returns
    -------
    str
        The value of the parameter.

    Raises
    ------
    ValueError
        If the parameter is not found and no default value is provided.

    Examples
    --------
    >>> from core_aws.ssm import get_parameter
    >>> get_parameter("/my/parameter")

    """
    try:
        if use_environ:
            secret_name = f'{secret_name}_{ENVIRONMENT}'
        get_secret_value_response = SECRET_CLIENT.get_secret_value(
            SecretId=secret_name
        )
        secret = get_secret_value_response['SecretString']
    except (KeyError, exceptions.ClientError) as e:
        print(f"Error: {e}")
        raise e
    else:
        LOGGER.debug(f"Value for {secret_name}: {secret}")
        if is_dict:
            secret = json.loads(secret)
        return secret
