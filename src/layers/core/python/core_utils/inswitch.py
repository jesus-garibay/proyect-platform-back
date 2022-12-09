# -*- coding: utf-8 -*-
"""
Helper functions for working with inswitch connection.
"""

import datetime
import json

import requests
from core_aws.dynamo import insert_request_log
from core_aws.secretsManager import get_secret
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger

INSWITCH_PARAMETERS = get_parameter('INSWITCH_HOST', use_environ=True)
BASE_URL = INSWITCH_PARAMETERS.get('host')
CREDENTIALS = get_secret('INSWITCH_CREDENTIALS', use_environ=True)
INSWITCH_TOKEN = CREDENTIALS.get('authorization_code')
PASSWORD = CREDENTIALS.get('password')
USERNAME = CREDENTIALS.get('user_name')
KYC_PASSWORD = CREDENTIALS.get('kyc_password')
KYC_USER = CREDENTIALS.get('kyc_user')
KYC_BASE_URL = INSWITCH_PARAMETERS.get('kyc_host')

CURRENCY = "PYG"
DEPOSIT_TYPE = "DEPOSIT"
SUBTYPE = "lending_credito"
DEBIT_PARTY = [{"key": "msisdn", "value": USERNAME}]
METADATA = [{"key": "CHANNEL", "value": "APP"}]

MONEY_PASSWORD = CREDENTIALS.get('take_money_out_pass')
MONEY_USERNAME = CREDENTIALS.get('take_money_out_user')
TRANSFER_TYPE = "TRANSFER"
CREDIT_PARTY = [{"key": "msisdn", "value": MONEY_USERNAME}]
MANUAL_METADATA = [{"key": "CHANNEL", "value": "APP"}, {"key": "externalDetails", "value": "MANUAL"}]

CONTENT_TYPE_JSON = 'application/json'

__all__ = [
    "get_token",
    "dispersion_credit",
    "get_token_kyc",
    "get_client_information_by_msisdn",
    "get_civil_status",
    "get_client_information_by_client_id",
    "get_balance_information_by_msisdn",
    "get_token_money",
    "dispersion_credit_money"
]

LAYER_NAME = 'layer-inswitch'
LOGGER = get_logger(LAYER_NAME)


def get_token():
    """
    Get a token to consult inswitch information.

    Returns
    -------
    str : token.

    Examples
    --------
    >>> from core_utils.inswitch import get_token
    >>> get_token()

    """
    url = BASE_URL + "/oauth2_provider/v1.0/token/authorize"
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Basic {INSWITCH_TOKEN}'}
    request_body = {"grant_type": 'password', "password": PASSWORD, "username": USERNAME, 'scope': 'write'}

    response = requests.post(url, headers=headers, data=request_body)
    response_body = response.json()
    response_status_code = response.status_code
    insert_request_log('inswitch', LAYER_NAME, 'get_token', 'post', url, headers, request_body, response_body,
                       response_status_code,
                       datetime.datetime.now())
    if response_status_code == 200:
        return response_body.get('access_token')


def dispersion_credit(body):
    """
    send to disperse a credit with inswitch

    Parameters
    ----------
    body : dict

    Returns
    -------
    requests response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import dispersion_credit
    >>> dispersion_credit({'body_example': 'value'})

    """
    token = get_token()
    if not token:
        return False
    url = BASE_URL + "/mts_api/v2.0/ins/transactions"
    headers = {'Content-Type': CONTENT_TYPE_JSON, 'Authorization': f'Bearer {token}'}

    body['currency'] = CURRENCY
    body['type'] = DEPOSIT_TYPE
    body['subType'] = SUBTYPE
    body['metadata'] = METADATA
    body['debitParty'] = DEBIT_PARTY

    response = requests.post(url, headers=headers, data=json.dumps(body))
    response_status_code = response.status_code
    response_body = response.json()

    insert_request_log('inswitch', LAYER_NAME, 'dispersion_credit', 'post', url, headers, body, response_body,
                       response_status_code,
                       datetime.datetime.now())

    LOGGER.info(f'status_code inswitch response: {response_status_code}')
    LOGGER.info(f'body inswitch response: {response_body}')

    return response


def get_token_kyc():
    """
    Get a token to consult inswitch information.

    Parameters
    ----------

    Returns
    -------
    str : token.

    Examples
    --------
    >>> from core_utils.inswitch import get_token_kyc
    >>> get_token_kyc()

    """
    url = KYC_BASE_URL + '/kyc-admin/kycadmin/autentication/login'
    headers = {'Content-Type': CONTENT_TYPE_JSON}

    request_body = {
        'userName': KYC_USER,
        'password': KYC_PASSWORD,
        'channel': 'APP',
        'application': 'LENDING'
    }

    response = requests.post(url, headers=headers, data=json.dumps(request_body))
    response_body = response.json()
    response_status_code = response.status_code
    insert_request_log('inswitch', LAYER_NAME, 'get_token_kyc', 'post', url, headers, request_body, response_body,
                       response_status_code,
                       datetime.datetime.now())
    if response_status_code == 200:
        return response_body.get('body').get('token')


def get_client_information_by_msisdn(msisdn):
    """
    Get a client information from mts.

    Parameters
    ----------

    Returns
    -------
    request response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import get_client_information_by_msisdn
    >>> get_client_information_by_msisdn('0912341234123')

    """
    LOGGER.info('getting Client Information by msisdn:' + msisdn)
    mts_token = get_token()
    headers = {'Authorization': f'Bearer {mts_token}', 'Content-Type': CONTENT_TYPE_JSON}
    url = BASE_URL + f'/mts_api_compat/v1.0/mm/accounts/msisdn@{msisdn}/accountinfo'

    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_client_information_by_msisdn status_code:{response_status_code}')
    LOGGER.info(f'get_client_information_by_msisdn body:{response_body}')
    insert_request_log('inswitch', LAYER_NAME, 'get_client_information_by_msisdn', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())
    return response


def get_civil_status(document):
    """
    Get civil status for a client in mts.

    Parameters
    ----------
    document: str
    Returns
    -------
    request response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import get_civil_status
    >>> get_civil_status('')

    """
    url = KYC_BASE_URL + f'/kyc-admin/kycadmin/documents/{document}'
    token = get_token_kyc()
    LOGGER.info('getting civilStatus:' + document)
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': CONTENT_TYPE_JSON}
    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_civil_status status_code:{response_status_code}')
    LOGGER.info(f'get_civil_status body:{response_body}')
    insert_request_log('inswitch', LAYER_NAME, 'get_civil_status', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())
    return response


def get_client_information_by_client_id(client_id):
    """
    Get a client information from mts.

    Parameters
    ----------
    client_id: str

    Returns
    -------
    request response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import get_client_information_by_client_id
    >>> get_client_information_by_client_id('0912341234123')

    """
    LOGGER.info('getting Client Information by client_id:' + client_id)
    mts_token = get_token()
    headers = {'Authorization': f'Bearer {mts_token}', 'Content-Type': CONTENT_TYPE_JSON}
    url = BASE_URL + f'/mts_api/v2.0/ins/accounts/client_id@{client_id}/accountinfo'

    response = requests.get(url, headers=headers)
    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_client_information_by_client_id status_code:{response_status_code}')
    LOGGER.info(f'get_client_information_by_client_id body:{response_body}')
    insert_request_log('inswitch', LAYER_NAME, 'get_client_information_by_client_id', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())
    return response


def get_balance_information_by_msisdn(msisdn):
    """
    Get a balance information from mts.

    Parameters
    ----------
    msisdn: str

    Returns
    -------
    request response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import get_balance_information_by_msisdn
    >>> get_balance_information_by_msisdn('0912341234123')

    """
    LOGGER.info('get_balance_information_by_msisdn:' + msisdn)
    mts_token = get_token()
    headers = {'Authorization': f'Bearer {mts_token}', 'Content-Type': CONTENT_TYPE_JSON,
               "Accept-Encoding": "gzip,deflate"}
    url = BASE_URL + f'/mts_api_compat/v1.0/mm/accounts/msisdn@{msisdn}/balance'

    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_balance_information_by_msisdn status_code:{response_status_code}')
    LOGGER.info(f'get_balance_information_by_msisdn body:{response_body}')
    insert_request_log('inswitch', LAYER_NAME, 'get_balance_information_by_msisdn', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())
    return response


def get_token_money():
    """
    Get a token money to consult inswitch information.

    Parameters
    ----------

    Returns
    -------
    str : token.

    Examples
    --------
    >>> from core_utils.inswitch import get_token_money
    >>> get_token_money()

    """
    url = BASE_URL + "/oauth2_provider/v1.0/token/authorize"
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Authorization': f'Basic {INSWITCH_TOKEN}'}
    request_body = {"grant_type": 'password', "password": MONEY_PASSWORD, "username": MONEY_USERNAME, 'scope': 'write'}

    response = requests.post(url, headers=headers, data=request_body)
    response_body = response.json()
    response_status_code = response.status_code
    insert_request_log('inswitch', LAYER_NAME, 'get_token_money', 'post', url, headers, request_body, response_body,
                       response_status_code,
                       datetime.datetime.now())
    if response_status_code == 200:
        return response_body.get('access_token')


def dispersion_credit_money(body):
    """
    send to disperse money a credit with inswitch

    Parameters
    ----------
    body : dict

    Returns
    -------
    requests response from inswitch.

    Examples
    --------
    >>> from core_utils.inswitch import dispersion_credit_money
    >>> dispersion_credit_money({'body_example': 'value'})

    """
    token = get_token_money()
    if not token:
        return False
    url = BASE_URL + "/mts_api/v2.0/ins/transactions"
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': CONTENT_TYPE_JSON,
               "Accept-Encoding": "gzip,deflate"}

    body['currency'] = CURRENCY
    body['type'] = TRANSFER_TYPE
    body['metadata'] = MANUAL_METADATA
    body['creditParty'] = CREDIT_PARTY

    response = requests.post(url, headers=headers, data=json.dumps(body))
    response_status_code = response.status_code
    response_body = response.json()

    insert_request_log('inswitch', LAYER_NAME, 'dispersion_credit_money', 'post', url, headers, body, response_body,
                       response_status_code,
                       datetime.datetime.now())

    LOGGER.info(f'status_code inswitch money response: {response_status_code}')
    LOGGER.info(f'body inswitch money response: {response_body}')

    return response
