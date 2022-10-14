# -*- coding: utf-8 -*-
import json
import logging

import boto3
from botocore import exceptions
from core_utils.environment import (
    ENVIRONMENT,
)

__all__ = ["get_parameter"]

LOGGER = logging.getLogger("layer-ssm")


def get_parameter(ssm_name, use_environ=False, default=None, is_dict=True):
    """
    Get a parameter from SSM service on aws.

    Parameters
    ----------
    is_dict : bool
    ssm_name : str
        The name of the parameter to get.
    use_environ : bool
        If True, the environment variable will be used to get the parameter.
    default : str
        The default value to return if the parameter is not found.

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
        ssm = boto3.client("ssm")
    except Exception as details:
        LOGGER.error("Error create client ssm")
        LOGGER.error("Details: {}".format(details))
        raise exceptions.ClientError
    try:
        if use_environ:
            ssm_name = f"{ssm_name}_{ENVIRONMENT}"
        parameters = ssm.get_parameter(Name=ssm_name)["Parameter"]["Value"]
    except Exception as details:
        LOGGER.warning(details)
        return default
    else:
        LOGGER.debug(f"Value for {ssm_name}: {parameters}")
        if is_dict:
            parameters = json.loads(parameters)

        return parameters
