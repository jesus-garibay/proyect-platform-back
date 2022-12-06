# -*- coding: utf-8 -*-
"""
Helper functions for working with inswitch connection.
"""
import datetime
import json

import requests
from core_aws.dynamo import insert_request_log
from core_aws.lambdas import call_lambda
from core_aws.secretsManager import get_secret
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger, get_timezone_datetime

CONTENT_TYPE_JSON = 'application/json'

__all__ = [
    "mambu_connection",
    "get_loan_by_loan_account_id",
    "get_schedule_status",
    "get_loan_by_loan_account_id_preview",
    "get_loans_by_criteria",
    "get_loan_by_loan_account_id_no_cache",
    "get_installments",
    "get_transactions_by_loan_account_id",
    "change_loan_status_by_id",
    "get_loans_status_client_account_holder"
]

MAMBU_CREDENTIALS = get_secret('MAMBU_CREDENTIALS', use_environ=True)
MAMBU_API_KEY = MAMBU_CREDENTIALS.get('api_key')
MAMBU_API_KEY_LOAN_LIFECYCLE_API_READ = MAMBU_CREDENTIALS.get('loan-lifecycle-api-read')
MAMBU_SETTINGS = get_parameter('MAMBU_SETTINGS', use_environ=True)
URL_BASE = MAMBU_SETTINGS.get('host')
LAMBDA_TO_INVOKE = MAMBU_SETTINGS.get('lambda_handler')

LAYER_NAME = 'layer-mambu'
LOGGER = get_logger(LAYER_NAME)


def mambu_connection(body):
    """
    invoke lambda from mambu

    Parameters
    ----------
    body : dict

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import mambu_connection
    >>> mambu_connection({'key_example': 'value_example'})

    """
    response = call_lambda('invoke-lambda-from-mambu', parameters=body,
                           arn=LAMBDA_TO_INVOKE)
    LOGGER.info(f'invoke-lambda-from-mambu response:{response}')

    insert_request_log('mambu', LAYER_NAME, 'mambu_connection', 'invoke_lambda', LAMBDA_TO_INVOKE, None, body,
                       response, None, datetime.datetime.now())
    return response


def get_loan_by_loan_account_id(loan_account_id, cache_data=False):
    """
    invoke endpoint from mambu to get loan information.

    Parameters
    ----------
    loan_account_id : str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_loan_by_loan_account_id
    >>> get_loan_by_loan_account_id('loan_account_id')

    """
    headers = {'apikey': MAMBU_API_KEY,
               "Accept-Encoding": "gzip,deflate",
               "Accept": "application/vnd.mambu.v2+json"}
    if cache_data:
        headers = {'apikey': MAMBU_API_KEY,
                   'Cache-Control': 'no-cache'}

    url = f"{URL_BASE}/loans/{loan_account_id}?detailsLevel=FULL"
    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_loan_by_loan_account_id status_code:{response_status_code}')
    LOGGER.info(f'get_loan_by_loan_account_id body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_loan_by_loan_account_id', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_schedule_status(loan_account_id):
    """
    invoke endpoint from mambu to get schedule status.

    Parameters
    ----------
    loan_account_id : str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_schedule_status
    >>> get_schedule_status('loan_account_id')

    """
    headers = {'apikey': MAMBU_API_KEY,
               "Accept-Encoding": "gzip,deflate",
               "Accept": "application/vnd.mambu.v2+json"}
    url = f"{URL_BASE}/loans/{loan_account_id}/schedule"

    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_schedule_status status_code:{response_status_code}')
    LOGGER.info(f'get_schedule_status body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_schedule_status', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_client_status(account_holder_key):
    """
    invoke endpoint from mambu to get schedule status.

    Parameters
    ----------
    account_holder_key : str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_client_status
    >>> get_client_status('get_client_status')

    """
    headers = {'apikey': MAMBU_API_KEY_LOAN_LIFECYCLE_API_READ,
               "Accept-Encoding": "gzip,deflate"}
    url = f"{URL_BASE}/clients/{account_holder_key}"

    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_client_status status_code:{response_status_code}')
    LOGGER.info(f'get_client_status body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_client_status', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_loan_by_loan_account_id_preview(loan_account_id, date=None):
    """
    invoke endpoint from mambu to get loan information.

    Parameters
    ----------
    loan_account_id : str
    date: datetime.datetime

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_loan_by_loan_account_id_preview
    >>> get_loan_by_loan_account_id_preview('loan_account_id', 'date')

    """
    date_to_send = date
    if not date:
        date_to_send = get_timezone_datetime('America/Asuncion')

    headers = {"apikey": MAMBU_API_KEY_LOAN_LIFECYCLE_API_READ,
               "Accept-Encoding": "gzip,deflate",
               "Accept": "application/vnd.mambu.v2+json",
               "content-type": "application/json;charset=UTF-8"}
    url = f"{URL_BASE}/loans/{loan_account_id}:previewPayOffAmounts"
    response = requests.post(url, headers=headers,
                             data=json.dumps({'valueDate': date_to_send.isoformat()}))

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_loan_by_loan_account_id_preview status_code:{response_status_code}')
    LOGGER.info(f'get_loan_by_loan_account_id_preview body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_loan_by_loan_account_id_preview', 'post', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_loans_by_criteria(body_criteria, limit=None, offset=None, pagination_details='ON'):
    """
        invoke endpoint from mambu to get loans by criteria.

        Parameters
        ----------
        body_criteria : dict
            dict with the information for the endpoint filters
        offset: int
            initial value for the request
        limit: int
            limit of elements by request
        pagination_details: String
            On or OFF information about pagination

        Returns
        -------
        dict: payload response from a lambda


        Examples
        --------
        >>> from core_utils.mambu import get_loans_by_criteria
        >>> params = {
        >>>    "filterCriteria": [
        >>>       {
        >>>          "field": "accountHolderKey",
        >>>          "operator": "EQUALS",
        >>>          "value": "8a44ba62811e64c80181445af9b060c7"
        >>>       }
        >>>    ],
        >>>    "sortingCriteria": {
        >>>       "field": "creationDate",
        >>>       "order": "ASC"
        >>>    }
        >>> }
        >>> get_loans_by_criteria(params)

        """
    data_post = {
        "headers": {'apikey': MAMBU_API_KEY,
                    "Accept-Encoding": "gzip,deflate",
                    "Accept": "application/vnd.mambu.v2+json"},
        "url": f"{URL_BASE}/loans:search",
        "json": body_criteria
    }
    if offset is not None and limit is not None:
        data_post.update({
            "params": {
                "paginationDetails": pagination_details,
                "limit": limit,
                "offset": offset
            }
        })

    response = requests.post(**data_post)

    response_status_code = response.status_code
    response_body = response.json()

    LOGGER.info(f'get_loans_by_criteria status_code:{response_status_code}')
    LOGGER.info(f'get_loans_by_criteria body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_loans_by_criteria', 'post', data_post.get('url'),
                       data_post.get('headers'), data_post.get('body_criteria'),
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_loan_by_loan_account_id_no_cache(loan_account_id):
    """
    invoke endpoint from mambu to get loan information.

    Parameters
    ----------
    loan_account_id : str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_loan_by_loan_account_id_no_cache
    >>> get_loan_by_loan_account_id_no_cache('loan_account_id')

    """

    response = get_loan_by_loan_account_id(loan_account_id, True)
    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_loan_by_loan_account_id_no_cache status_code:{response_status_code}')
    LOGGER.info(f'get_loan_by_loan_account_id_no_cache body:{response_body}')
    return response


def get_installments(due_from, due_to, offset=0, limit=50):
    """
    invoke endpoint from mambu to get installments to be charged.

    Parameters
    ----------
    limit: int
    offset: int
    due_from: str
    due_to: str

    Returns
    -------
    dict: payload response from a lambda

    Examples
    --------
    >>> from core_utils.mambu import get_installments
    >>> get_installments('2022-06-15')

    """

    _headers = {
        "Accept-Encoding": "gzip,deflate",
        "Accept": 'application/vnd.mambu.v2+json',
        "apikey": MAMBU_API_KEY,
    }
    _parameters = {
        "paginationDetails": 'OFF',
        "dueFrom": due_from,
        "dueTo": due_to,
        "limit": limit,
        "offset": offset
    }
    try:
        response = requests.get("{url}/installments".format(url=URL_BASE), headers=_headers, params=_parameters)
    except Exception as error:
        LOGGER.error("Error while calling Mambu. {error}".format(error=error))
        return None

    return response


def get_transactions_by_loan_account_id(loan_account_id):
    """
    invoke endpoint from mambu to get loan transactions.

    Parameters
    ----------
    loan_account_id : str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_aws.lambdas import get_transactions_by_loan_account_id
    >>> get_transactions_by_loan_account_id('loan_account_id')

    """
    headers = {'apikey': MAMBU_API_KEY,
               "Accept-Encoding": "gzip,deflate",
               "Accept": "application/vnd.mambu.v2+json"}
    url = f"{URL_BASE}/loans/{loan_account_id}/transactions"
    response = requests.get(url, headers=headers)

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_transactions_by_loan_account_id status_code:{response_status_code}')
    LOGGER.info(f'get_transactions_by_loan_account_id body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_transactions_by_loan_account_id', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def change_loan_status_by_id(loan_account_id, idempotency_key, action="CLOSE"):
    """
    invoke endpoint from mambu to get loan transactions.

    Parameters
    ----------
    loan_account_id : str
    idempotency_key: str
    action: str

    Returns
    -------
    dict: payload response from a lambda


    Examples
    --------
    >>> from core_utils.mambu import change_loan_status_by_id
    >>> change_loan_status_by_id('loan_account_id', 'idempotency_key')

    """
    headers = {'apikey': MAMBU_API_KEY_LOAN_LIFECYCLE_API_READ,
               "Content-Type": "Application/json",
               "Accept": "application/vnd.mambu.v2+json",
               "Idempotency-Key": idempotency_key}

    url = f"{URL_BASE}/loans/{loan_account_id}:changeState"
    response = requests.post(url, headers=headers, data=json.dumps({"action": action}))

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'change_loan_status_by_id status_code:{response_status_code}')
    LOGGER.info(f'change_loan_status_by_id body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'change_loan_status_by_id', 'post', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response


def get_loans_status_client_account_holder(account_holder, status_loan=4):
    """
    invoke endpoint from mambu to loans:search.
    this endpoint get can information aboud all loans in specific status established

    Args:
        account_holder : An str that represents the value ot the accountHolderKey
        status_loan: An int that represents the status of the loans that will be retrieved

    Returns:
        dict: mambu api payload response containing the credits of the client with the requested status

    Example:
        >>> from core_utils.mambu import get_loans_status_client_account_holder
        >>> get_loans_status_client_account_holder('account_holder',1)

    """

    status = {1: "PARTIAL_APPLICATION", 2: "PENDING_APPROVAL",
              3: "APPROVED", 4: "ACTIVE", 5: "ACTIVE_IN_ARREARS", 6: "CLOSED"}
    post_body = f"""
                    {{
                      "filterCriteria": [
                        {{
                          "field": "accountHolderKey",
                          "operator": "EQUALS",
                          "value": "{account_holder}"
                        }},
                        {{
                          "field": "accountState",
                          "operator": "EQUALS",
                          "value": "{status[status_loan]}"
                        }}
                      ],
                      "sortingCriteria": {{
                        "field": "encodedKey",
                        "order": "ASC"
                      }}
                    }}
                """

    headers = {'apikey': MAMBU_API_KEY,
               "Accept-Encoding": "gzip,deflate",
               "Accept": "application/vnd.mambu.v2+json"}
    url = f"{URL_BASE}/loans:search"
    response = requests.post(url, headers=headers, json=json.loads(post_body))

    response_status_code = response.status_code
    response_body = response.json()
    LOGGER.info(f'get_loans_status_client_account_holder status_code:{response_status_code}')
    LOGGER.info(f'get_loans_status_client_account_holder body:{response_body}')
    insert_request_log('mambu', LAYER_NAME, 'get_loans_status_client_account_holder', 'get', url, headers, None,
                       response_body,
                       response_status_code,
                       datetime.datetime.now())

    return response
