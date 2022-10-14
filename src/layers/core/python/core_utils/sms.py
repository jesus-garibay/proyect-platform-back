# -*- coding: utf-8 -*-
"""
Helper functions for working with mfs_lending connection.
"""

import datetime

import requests
from core_aws.dynamo import insert_request_log
from core_aws.secretsManager import get_secret
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger

MFS_LENDING_PARAMETERS = get_parameter('MFS_LENDING', use_environ=True)
BASE_URL = MFS_LENDING_PARAMETERS.get('host')

MFS_LENDING_CREDENTIALS = get_secret('MFS_LENDING_CREDENTIALS', use_environ=True)
CLIENT_ID = MFS_LENDING_CREDENTIALS.get('client_id')
CLIENT_SECRET = MFS_LENDING_CREDENTIALS.get('secret')

__all__ = [
    "get_token",
    "send_sms",
    "parse_body"
]

LAYER_NAME = 'layer-sms'
LOGGER = get_logger(LAYER_NAME)


def get_token(refresh_token=False):
    """
    Get a token to consult mfs_lending information.

    Parameters
    ----------
    Returns
    -------
    str : token.

    Examples
    --------
    >>> from core_utils.sms import get_token
    >>> get_token()

    """
    path = 'refresh_accesstoken' if refresh_token else 'accesstoken'
    url = BASE_URL + f"/oauth/client_credential/{path}?grant_type=client_credentials"

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    request_body = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}

    response = requests.post(url, headers=headers, data=request_body)
    response_body = parse_body(response)
    response_status_code = response.status_code
    LOGGER.info('invoke get_token method in sms flow')
    LOGGER.info(f'response status_code: {response_status_code}')
    LOGGER.info(f'response body: {response_body}')
    insert_request_log('mfs_lending', LAYER_NAME, 'get_token', 'post', url, headers, request_body, response_body,
                       response_status_code,
                       datetime.datetime.now())

    if response_status_code == 200:
        return response_body.get('access_token')


def send_sms(body):
    """
    send sms with mfs_lending

    Parameters
    ----------
    body : dict

    Returns
    -------
    requests response from mfs_lending.

    Examples
    --------
    >>> from core_utils.inswitch import dispersion_credit
    >>> dispersion_credit({'from': 'value', 'to': 'value', 'message'})

    """
    token = get_token()
    if not token:
        token = get_token(True)
        if not token:
            return False

    url = BASE_URL + "/v1/tigo/mobile/kannel/sendsms"
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(url, headers=headers, params=body)
    response_status_code = response.status_code
    response_body = parse_body(response)

    LOGGER.info('invoke send_sms method in sms flow')
    LOGGER.info(f'response status_code: {response_status_code}')
    LOGGER.info(f'response body: {response_body}')
    insert_request_log('mfs_lending', LAYER_NAME, 'send_sms', 'get', url, headers, body, response_body,
                       response_status_code,
                       datetime.datetime.now())

    LOGGER.info(f'status_code mfs_lending response: {response_status_code}')
    LOGGER.info(f'body mfs_lending response: {response}')

    return response


def parse_body(response):
    """
    parse requests response to a dict.

    Parameters
    ----------
    Returns
    -------
    requets : response.

    Examples
    --------
    >>> from core_utils.sms import parse_body
    >>> parse_body(requests.models.Response)

    """
    try:
        response_body = response.json()
    except Exception as error:
        LOGGER.warning(str(error))
        response_body = response.text
    if not isinstance(response_body, dict):
        response_body = {'response': response_body}
    return response_body
