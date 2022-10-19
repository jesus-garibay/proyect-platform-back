# -*- coding: utf-8 -*-
"""
Helper functions for working with braze connection.
"""

import datetime
import json
import requests
from core_aws.dynamo import insert_request_log
from core_aws.secretsManager import get_secret
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger

__all__ = [
    "get_token",
    "send_event_to_braze"
]

BRAZE_PARAMETERS = get_parameter('BRAZE_HOST', use_environ=True)
BASE_URL = BRAZE_PARAMETERS.get('host')
CREDENTIALS = get_secret('BRAZE_CREDENTIALS', use_environ=True)
PASSWORD = CREDENTIALS.get('password')
USERNAME = CREDENTIALS.get('username')

LAYER_NAME = 'layer-braze'
CONTENT_TYPE_JSON = 'application/json'
LOGGER = get_logger(LAYER_NAME)


def get_token():
    """
    Get a token to send sms with braze .

    Returns
    -------
    str : token.

    Examples
    --------
    >>> from core_utils.braze import get_token
    >>> get_token()

    """
    url = BASE_URL + "/oauth/client_credential/accesstoken?grant_type=client_credentials"

    response = requests.post(url, auth=(USERNAME, PASSWORD))

    headers = {}

    response_token = response.json()
    response_status_code = response.status_code
    insert_request_log('braze', LAYER_NAME, 'get_token', 'post', url, headers, None, response_token,
                       response_status_code,
                       datetime.datetime.now())
    if response_status_code == 200:
        return response_token.get('access_token')


def send_event_to_braze(event_header, customer_profile, event_data):
    """
    send event to braze

    Parameters
    ----------
    event_header : dict
    customer_profile : dict
    event_data : dict


    Returns
    -------
    requests response from braze.

    Examples
    --------
    >>> from core_utils.braze import send_event_to_braze
    >>> send_event_to_braze({

      "country":"PY",

      "customer_type":"prepaid_mobile",

      "customer_action":"onboarding",

      "event_name":"MFS_D_EXPIRACION_DA_ACTIVO",

      "event_code":"MFS_D_EXPIRACION_DA_ACTIVO",

      "event_description":"MFS_D_EXPIRACION_DA_ACTIVO",

      "event_source":"Lending",

      "event_uid":"test-MFS_D_EXPIRACION_DA_ACTIVO"

   },
   {

      "phone_number_main_contact":"984223595"

   },
   {

      "monto":150000,

      "fecha":"06/30"


   }
   )

    """
    token = get_token()
    if not token:
        return False
    url = BASE_URL + "/v1/tigo/eventbroker/events"
    headers = {'Content-Type': CONTENT_TYPE_JSON, 'Authorization': f'Bearer {token}'}
    body = {
        'event_header': event_header,
        'customer_profile': customer_profile,
        'event_data': event_data
    }
    response = requests.post(url, headers=headers, data=json.dumps(body))
    response_status_code = response.status_code
    response_body = response.json()

    insert_request_log('braze', LAYER_NAME, 'send_event_to_braze', 'post', url, headers, body, response_body,
                       response_status_code,
                       datetime.datetime.now())

    LOGGER.info(f'status_code braze response: {response_status_code}')
    LOGGER.info(f'body braze response: {response_body}')

    return response
