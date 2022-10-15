# -*- coding: utf-8 -*-
import json
import uuid

import boto3
from core_utils.utils import get_logger

__all__ = [
    "get_table",
    "insert_request_log"
]

LOGGER = get_logger("layer-dynamo")


def get_table(table_name):
    """
    get a table from dynamo.

    Parameters
    ----------
    table_name : str

    Returns
    -------
    dynamo table.

    Examples
    --------
    >>> from core_aws.dynamo import get_table
    >>> get_table('table_name_dynamo')

    """
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table_name)
    return table


def insert_request_log(service_name, lambda_or_layer_name, function_name, http_type_method, url, headers, body,
                       response_body, response_status_code, created_date):
    """
    insert request services into a log table.

    Parameters
    ----------
    service_name : str
    lambda_or_layer_name: str
    function_name: str
    http_type_method: str
    url : str
    headers : dict
    body : dict
    response_body : dict
    response_status_code : int
    created_date : datetime.datetime

    Returns
    -------
    a boolean, True if insert was success, and False if insert was failure.

    Examples
    --------
    >>> from core_aws.dynamo import insert_request_log
    >>> insert_request_log('service_name', 'function_name', 'http_type_method','https://url', {'headers_example': 'value'}, {'body_example': 'value'},
    >>>                    {'response_body_example': 'value'}, 200, datetime.datetime.now())

    """
    log_table = get_table('LogRequestsToServices')
    try:
        log_table_insert = log_table.put_item(Item={
            "ServiceRequestName": service_name,
            "ServiceRequestID": f'{service_name}-{uuid.uuid4()}',
            "LambdaOrLayerName": lambda_or_layer_name,
            "FunctionName": function_name,
            "HttpTypeMethod": http_type_method,
            "Url": url,
            "Headers": json.dumps(headers) if headers else headers,
            "RequestBody": json.dumps(body) if body else body,
            "ResponseBody": json.dumps(response_body) if response_body else response_body,
            "ResponseStatusCode": response_status_code,
            "CreatedDate": str(created_date)
        })
    except Exception as error:
        LOGGER.error(f'Error message: {error}')
        return False

    if 'ResponseMetadata' not in log_table_insert or log_table_insert['ResponseMetadata']['HTTPStatusCode'] != 200:
        LOGGER.error('Error to insert the request to service in the log table')
        return False
    LOGGER.info('insert the request to service in the log table was success')
    return True
