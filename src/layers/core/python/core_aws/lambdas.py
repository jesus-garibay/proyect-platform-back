# -*- coding: utf-8 -*-
import json
import os
import uuid

import boto3
from core_utils.utils import get_logger

__all__ = [
    "create_context",
    "call_lambda",
    "call_lambda_async"
]

LAYER_NAME = 'layer-lambdas'
LOGGER = get_logger(LAYER_NAME)


def create_context(function_name):
    """
    Create a context for a lambda function.

    Parameters
    ----------
    function_name : str

    Returns
    -------
    Type: context for a lambda function


    Examples
    --------
    >>> from core_aws.lambdas import create_context
    >>> create_context("lambda_function_name")

    """
    definition = {
        "get_remaining_time_in_millis": lambda: 30000,
        "function_name": function_name,
        "aws_request_id": str(uuid.uuid4()),
    }
    return type("Context", (), definition)


def call_lambda(lambda_name, parameters, arn=False):
    """
    call a lambda depending on the name.
    Parameters
    ----------
    lambda_name
    parameters
    arn
    Returns {statusCode:int,body:{}}
    -------
    Examples
    --------
    >>> from core_aws.lambdas import call_lambda
    >>> call_lambda('name_your_lambda',{pathParameters: {},body:{}})
    """

    client = boto3.client('lambda')

    if not arn:
        if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
            path = os.environ['AWS_LAMBDA_FUNCTION_NAME']
            split = path.split('-')
            environment = split[0]
            app_name = split[1]
        else:
            environment = os.environ.get("Environment")
            app_name = os.environ.get('app_name')

        lambda_to_call = environment + "-" + app_name + "-" + lambda_name
    else:
        lambda_to_call = arn

    LOGGER.info(f'Lambda name to invoke: {lambda_to_call}')
    response = client.invoke(
        FunctionName=lambda_to_call,
        InvocationType='RequestResponse',
        Payload=json.dumps(parameters),
    )
    LOGGER.info(f'Payload to send: {parameters}')
    LOGGER.info(f'response: {response}')
    return json.load(response['Payload'])


def call_lambda_async(lambda_name, parameters):
    """
    call a lambda depending on the name.
    Parameters
    ----------
    lambda_name
    parameters
    Returns {statusCode:int,body:{}}
    -------
    Examples
    --------
    >>> from core_aws.lambdas import call_lambda
    >>> call_lambda_async('name_your_lambda',{pathParameters: {},body:{}})
    """

    client = boto3.client('lambda')

    if "AWS_LAMBDA_FUNCTION_NAME" in os.environ:
        path = os.environ['AWS_LAMBDA_FUNCTION_NAME']
        split = path.split('-')
        environment = split[0]
        app_name = split[1]
    else:
        environment = os.environ.get("Environment")
        app_name = os.environ.get('app_name')

    lambda_to_call = environment + "-" + app_name + "-" + lambda_name

    response = client.invoke(
        FunctionName=lambda_to_call,
        InvocationType='Event',
        Payload=json.dumps(parameters),
    )
    LOGGER.info(f'Payload to send lambda async {lambda_to_call}: {parameters}')
    LOGGER.info(f'response invoke async {lambda_to_call}: {response}')
    return response
