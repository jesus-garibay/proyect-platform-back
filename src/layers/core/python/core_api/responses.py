# -*- coding: utf-8 -*-
import json

from core_utils.utils import (
    cast_default,
)
from core_utils.utils import get_logger

__all__ = [
    "api_response",
    "create_body",
    "SUCCESSFUL_CODE",
    "NOT_FOUND_CODE",
    "NOT_FOUND_CODE_GENERAL",
    "ERROR_SERVER_CODE",
]

SUCCESSFUL_CODE = 200
NOT_FOUND_CODE = 404
NOT_FOUND_CODE_GENERAL = 400
ERROR_SERVER_CODE = 500


LAYER_NAME = 'layer-api-responses'
LOGGER = get_logger(LAYER_NAME)


def create_body(response, message=None, error=None):
    """
        Parse the lambda response and return a dict with the http response.
        Parameters
        ----------
        response : Any
            The body of the lambda response.
        message : Str
            The message response
        error : Str
            The error code

        Returns
        -------
        dict
            The response to be returned to the client.

        Examples
        --------
        >>> from core_api.responses import create_body
        >>> create_body({"foo": "bar"}, 200)

        """
    body = {
        "response_code": "0",
        "description": "SUCCESS",
        "response":  []
    }

    if response is not None:
        body['response'] = response

        if error is None:
            LOGGER.info({'SUCCESS_RESPONSE': body})
            return body

    response_code = 'PYL' + error

    LOGGER.error({'Error '+response_code: message})
    body['response_code'] = response_code
    body['description'] = message

    return body


def api_response(body, status_code):
    """
    Parse the lambda response and return a dict with the http response.
    Parameters
    ----------
    body : Any
        The body of the lambda response.
    status_code : int

    Returns
    -------
    dict
        The response to be returned to the client.

    Examples
    --------
    >>> from core_api.responses import api_response
    >>> api_response({"foo": "bar"}, 200)

    """
    try:
        body = json.dumps(body, default=cast_default, ensure_ascii=False)
    except Exception as details:
        print(str(details))
        raise details
    else:
        response = {
            "statusCode": status_code,
            "body": body,
            "headers": {"Access-Control-Allow-Origin": "*"},
        }
        return response
