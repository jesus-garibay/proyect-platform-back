# -*- coding: utf-8 -*-
import os

import boto3
from botocore.exceptions import (
    ClientError,
)
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger

__all__ = [
    "get_cognito_headers",
    "get_token_cognito",
    "create_new_user",
    "UsernameExistsException",
    "set_admin_user_password",
    "admin_confirm_sign_up",
    "admin_update_user_attributes"
]

LAYER_NAME = 'layer-cognito'
LOGGER = get_logger(LAYER_NAME)


def get_cognito_headers(*, region, client_id, username, password, user_pool_id, domain):
    """
    Get the headers for the request to cognito.

    Parameters
    ----------
    region : str
        Region where the cognito instance is located.
    client_id : str
        Client id of the cognito instance client.
    username : str
        Username for login.
    password : str
        Password for login.
    user_pool_id : str
        User pool id of the cognito instance.
    domain : str
        Domain where the cognito instance is located.

    Returns
    -------
    dict
        Headers for the request to cognito.

    Examples
    --------
    >>> from core_aws.cognito import get_cognito_headers
    >>> get_cognito_headers('us-east-1', 'client_id', 'username', 'password', 'user_pool_id', 'domain')

    """
    client = boto3.client(
        "cognito-idp",
        aws_access_key_id="",
        aws_secret_access_key="",
        region_name=region,
    )
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
        ClientMetadata={"UserPoolId": user_pool_id},
    )

    headers = {
        "Authorization": f"Bearer {response.get('AuthenticationResult').get('IdToken')}",
        "content-type": "application/json",
    }
    return headers, domain


def get_token_cognito(
        *,
        client_id,
        username,
        password,
        user_pool_id,
        region_name="us-east-1",
        auth_flow="USER_PASSWORD_AUTH",
        bearer=True,
):
    """
    Get the token for the request to cognito.

    Parameters
    ----------
    client_id : str
        Client id of the cognito instance client.
    username : str
        Username for login.
    password : str
        Password for login.
    user_pool_id : str
        User pool id of the cognito instance.
    region_name : str
        Region where the cognito instance is located.
        us-east-1 by default.
    auth_flow : str
        Authentication flow.
        USER_PASSWORD_AUTH by default.
    bearer : bool
        If True, return the token as a bearer token.
        True by default.

    Returns
    -------
    str
        Token for the request to cognito.
        Bearer TOKEN if bearer param is true
        TOKEN if the bearer param is false

    Examples
    --------
    >>> from core_aws.cognito import get_token_cognito
    >>> get_token_cognito('client_id', 'username', 'password', 'user_pool_id')

    """
    client = boto3.client("cognito-idp", region_name=region_name)
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow=auth_flow,
        AuthParameters={"USERNAME": username, "PASSWORD": password},
        ClientMetadata={"UserPoolId": user_pool_id},
    )
    token = response.get("AuthenticationResult", {}).get("IdToken")
    if bearer:
        return f"Bearer {token}"
    else:
        return token


def create_new_user(*, email, parent=None, region="us-east-1"):
    """
    Create a new user in cognito user pool.

    Parameters
    ----------

    email : str
        email for login.
    parent : str
        .
    region : str
        Region where the cognito instance is located.
        us-east-1 by default.

    Returns
    -------
    dict
        a dict with the data for user created

    Examples
    --------
    >>> from core_aws.cognito import create_new_user
    >>> create_new_user('username', 'password', True, 'us-east-1')

    """
    client = boto3.client("cognito-idp", region)
    parameter_name_pool_id = f'LENDING_POOL_ID_{os.getenv("ENVIRONMENT")}'
    try:
        user_attributes = [{"Name": "email", "Value": email}]
        if parent:
            user_attributes.append({"Name": "custom:parent", "Value": parent})
        response = client.admin_create_user(
            UserPoolId=os.getenv(parameter_name_pool_id) or get_parameter(parameter_name_pool_id, is_dict=False),
            Username=email,
            UserAttributes=user_attributes,
            ValidationData=[{"Name": "email", "Value": email}],
        )
    except ClientError as e:
        if "UsernameExistsException" in str(e):
            raise UsernameExistsException(str(e))
        else:
            raise e
    return response


class UsernameExistsException(Exception):
    def __init__(self, message):
        super().__init__(message)


def set_admin_user_password(username, password, permanent=True, region="us-east-1"):
    """
    Set the password to change the status FORCE_CHANGE_PASSWORD to CONFIRMED.

    Parameters
    ----------

    username : str
        Username for login.
    password : str
        Password for login.
    permanent : bool
        True if the password is permanent, False if it is temporary.
    region : str
        Region where the cognito instance is located.
        us-east-1 by default.

    Returns
    -------
    dict
        return False is request is different from 200 and return response http request is the password was successfully
        set

    Examples
    --------
    >>> from core_aws.cognito import set_admin_user_password
    >>> set_admin_user_password('username', 'password', True, 'us-east-1')

    """
    client = boto3.client("cognito-idp", region)
    parameter_name_pool_id = f'LENDING_POOL_ID_{os.getenv("ENVIRONMENT")}'
    try:
        response = client.admin_set_user_password(
            UserPoolId=os.getenv(parameter_name_pool_id) or get_parameter(parameter_name_pool_id, is_dict=False),
            Username=username,
            Password=password,
            Permanent=permanent
        )
    except Exception as error:
        LOGGER.exception(f'error to admin set user password in cognito: {error}')
        return False

    if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        return False

    return response


def admin_confirm_sign_up(username, client_metadata=None, region="us-east-1"):
    """
    Confirms user registration as an admin without using a confirmation code. Works on any user.
    Calling this action requires developer credentials.

    Parameters
    ----------
    username : str
        Username for login.
    client_metadata : dict
        client metadata in cognito.
    region : str
        Region where the cognito instance is located.
        us-east-1 by default.

    Returns
    -------
    dict
        return False is request is different from 200 and return response http request is the password was successfully
        set

    Examples
    --------
    >>> from core_aws.cognito import admin_confirm_sign_up
    >>> admin_confirm_sign_up('username', {}, 'us-east-1')

    """
    client = boto3.client("cognito-idp", region)
    parameter_name_pool_id = f'LENDING_POOL_ID_{os.getenv("ENVIRONMENT")}'
    admin_confirm_sign_up_params = {
        "UserPoolId": os.getenv(parameter_name_pool_id) or get_parameter(parameter_name_pool_id, is_dict=False),
        "Username": username
    }
    if client_metadata:
        admin_confirm_sign_up_params.update({'ClientMetadata': client_metadata})

    try:
        response = client.admin_confirm_sign_up(**admin_confirm_sign_up_params)
    except Exception as error:
        LOGGER.exception(f'error to admin set user password in cognito: {error}')
        return False

    if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        return False

    return response


def admin_update_user_attributes(username, user_attributes, client_metadata=None, region="us-east-1"):
    """
    Confirms user registration as an admin without using a confirmation code. Works on any user.
    Calling this action requires developer credentials.

    Parameters
    ----------
    username : str
        Username for login.
    user_attributes : list
        attributes of the user in cognito.
    client_metadata : dict
        client metadata in cognito.
    region : str
        Region where the cognito instance is located.
        us-east-1 by default.

    Returns
    -------
    dict
        return False is request is different from 200 and return response http request is the password was successfully
        set

    Examples
    --------
    >>> from core_aws.cognito import admin_update_user_attributes
    >>> admin_update_user_attributes('username', {}, {}, 'us-east-1')

    """
    client = boto3.client("cognito-idp", region)
    parameter_name_pool_id = f'LENDING_POOL_ID_{os.getenv("ENVIRONMENT")}'
    admin_update_user_attributes_params = {
        "UserPoolId": os.getenv(parameter_name_pool_id) or get_parameter(parameter_name_pool_id, is_dict=False),
        "Username": username,
        "UserAttributes": user_attributes
    }
    if client_metadata:
        admin_update_user_attributes_params.update({'ClientMetadata': client_metadata})

    try:
        response = client.admin_update_user_attributes(**admin_update_user_attributes_params)
    except Exception as error:
        LOGGER.exception(f'error to admin set user password in cognito: {error}')
        return False

    if response.get('ResponseMetadata', {}).get('HTTPStatusCode') != 200:
        return False

    return response
