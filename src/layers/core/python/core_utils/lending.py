# -*- coding: utf-8 -*-
"""
Helper functions for working with lending database get information.
"""
import datetime
import uuid
from decimal import Decimal

from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from core_api.utils import get_status_code, get_body
from core_aws.dynamo import get_table
from core_aws.lambdas import call_lambda, call_lambda_async
from core_utils.inswitch import (
    get_client_information_by_msisdn,
    get_client_information_by_client_id
)
from core_utils.mambu import get_loan_by_loan_account_id_preview
from core_utils.utils import get_logger

_OFFER_NOT_FOUND = 'Offer not found'
_LOAN_NOT_FOUND = 'Loan not found'
_STATUS_LOAN_NOT_FOUND = 'Loan not found'
_STATUS_PREPPROVED_NOT_FOUND = 'Status preapproved not found'
_CLIENT_NOT_FOUND = 'Client not found'
_CLIENT_INSWITCH_NOT_FOUND = 'Client InSwitch not found'

__all__ = [
    "find_information_by_lambda",
    "find_product_by_id",
    "create_inswitch_transactions",
    "update_dynamic_fields_in_dynamo",
    "get_total_balance_mambu",
    "LendingException",
    "LendingPaymentException",
    "find_information_by_lambda_async",
    "update_loan",
    "delete_item_from_table",
    "find_by_client_by_idmts",
    "find_by_client_by_cell_number",
    "compare_client_data",
    "create_row_in_dynamo",
    "get_item_from_dynamo",
    "get_items_by_query_from_dynamo",
    "get_loans_by_client",
    "find_tigo_point_name",
    "register_new_client_sms",
    "validate_access",
    "find_loan_by_client",
    "find_status_by_id",
    "find_offer_by_client",
    "get_movements_from_loan_offers_movements_by_client",
    "get_last_loan"
]

LAYER_NAME = 'layer-lending'
LOGGER = get_logger(LAYER_NAME)


def find_information_by_lambda(client, lambda_name, payload=None, validate_response=True):
    """
    invoke lambda to get loan from a client.
    Parameters
    ----------
    client : str
    lambda_name: str
    payload: dict
    validate_response: bool
    Returns
    -------
    dict: payload response from a lambda
    Examples
    --------
    >>> from core_aws.lambdas import find_information_by_lambda
    >>> find_information_by_lambda("client", "lambda_name", "payload")
    """
    if payload is None:
        payload = {
            "pathParameters": {
                "client": client
            }
        }

    response = call_lambda(lambda_name, payload)

    if validate_response:
        status_code = get_status_code(response)
        LOGGER.info(f'response statusCode: {status_code}')
        if response is None or status_code not in [200, 204]:
            LOGGER.error(f'error to invoke in lambda: {lambda_name}')
            return {'message': 'Error to get Information'}

        body = get_body(response)
        LOGGER.info(f'response body: {body}')
        return body

    return response


def find_product_by_id(product):
    """
    invoke lambda to get product information.
    Parameters
    ----------
    product : int
    Returns
    -------
    dict: payload response from a lambda
    Examples
    --------
    >>> from core_aws.lambdas import find_product_by_id
    >>> find_product_by_id(1)
    """
    params = {
        "pathParameters": {
            "product": product
        }
    }

    response = call_lambda("get_product_by_id", params)
    status_code = get_status_code(response)
    LOGGER.info(f'response statusCode: {status_code}')
    if response is None or status_code != 200:
        LOGGER.error('error to invoke in lambda: get_product_by_id')
        raise TypeError('error when looking for product')

    body = get_body(response)
    LOGGER.info(f'response body: {body}')
    return body


def create_inswitch_transactions(client_id, loan_id, idempotency_key, request_id, transaction_type):
    """
    insert inswitchTransaction table.
    Parameters
    ----------
    client_id : str
    loan_id: int
    idempotency_key: str
    request_id: str
    transaction_type : str
    Returns
    -------
    a boolean, True if insert was success, and False if insert was failure.
    Examples
    --------
    >>> from core_aws.dynamo import create_inswitch_transactions
    >>> create_inswitch_transactions('client_id', 'idempotency_key', 'request_id','transaction_type')
    """
    try:
        localtime = datetime.datetime.now()
        item = {
            "IdempotencyKey": idempotency_key,
            "RequestId": request_id,
            "IdClient": client_id,
            "LoanId": loan_id,
            "InswitchStatus": "inProgress",
            "CreatedDate": str(localtime.isoformat(timespec='seconds')),
            "UpdatedDate": str(localtime.isoformat(timespec='seconds')),
            "Requester": {'RequestId': request_id,
                          'IdempotencyKey': idempotency_key},
            "transactionType": transaction_type
        }
        table = get_table('InswitchTransaction')
        dynamo_insert = table.put_item(Item=item)
        if 'ResponseMetadata' not in dynamo_insert and dynamo_insert['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.info('error to create the record in mambuTransaction')
            return False

        LOGGER.info('insert in inswitch transaction was successfully')
        return True
    except Exception as error:
        LOGGER.info('error to create the record in mambuTransaction')
        LOGGER.error("Exception Message [%s]" % error)
        return False


def update_dynamic_fields_in_dynamo(table_name, key, _fields_to_update, update_date_field=None):
    """
    insert dynamic field in a table.
    Parameters
    ----------
    table_name: str
    key: dict
    _fields_to_update: dict
    update_date_field: str
    Returns
    -------
    a boolean, True if insert was success, and False if insert was failure.
    Examples
    --------
    >>> from core_aws.dynamo import update_dynamic_fields_in_dynamo
    >>> update_dynamic_fields_in_dynamo('table_name', {'key': 'value'}, {'key': 'value'}, 'update_field')
    """
    LOGGER.info('invoke method update_dynamic_fields_in_dynamo')
    LOGGER.info(f'table_name: {table_name}')
    LOGGER.info(f'key: {key}')
    localtime = datetime.datetime.now()
    if update_date_field:
        _fields_to_update.update({update_date_field: str(localtime.isoformat(timespec='seconds'))})

    LOGGER.info(f'_fields_to_update: {_fields_to_update}')
    _update_expression = 'set '
    _values_expression = {}
    _expression_attribute_names = {}

    index = 1
    for _field, _value in _fields_to_update.items():
        if index == 1:
            _update_expression += f'#{_field}= :{_field}'
        else:
            _update_expression += f', #{_field}= :{_field}'

        if isinstance(_value, bool):
            _value = bool(_value)
        elif isinstance(_value, int):
            _value = int(_value)
        elif isinstance(_value, float):
            _value = Decimal(str(_value))
        _expression_attribute_names.update({f'#{_field}': _field})
        _values_expression.update({f':{_field}': _value})
        index += 1

    try:
        table = get_table(table_name)
        response = table.update_item(
            Key=key,
            UpdateExpression=_update_expression,
            ExpressionAttributeValues=_values_expression,
            ExpressionAttributeNames=_expression_attribute_names
        )
    except Exception as error:
        LOGGER.error(f'Exception Message {error}')
        return False

    if 'ResponseMetadata' not in response or response['ResponseMetadata']['HTTPStatusCode'] != 200:
        return False

    return True


def get_total_balance_mambu(loan_account_id):
    """
    get balance información from mambu.
    Parameters
    ----------
    loan_account_id: str
    Returns
    -------
    a balance información from mambu
    Examples
    --------
    >>> from core_aws.dynamo import get_total_balance_mambu
    >>> get_total_balance_mambu('loan_account_id')
    """
    response = get_loan_by_loan_account_id_preview(loan_account_id)
    response_status_code = response.status_code
    if response_status_code != 200:
        raise LendingException('Error to get balance from mambu')

    response_body = response.json()
    balance = float(response_body.get('totalBalance'))
    if balance != 0.0 and not balance:
        raise LendingException('Error to get balance from mambu')

    return balance


class LendingException(Exception):
    def __init__(self, message):
        super().__init__(message)


class LendingPaymentException(Exception):
    def __init__(self, message):
        super().__init__(message)


def find_information_by_lambda_async(client, lambda_name, payload=None):
    """
    invoke lambda async.
    Parameters
    ----------
    client : str
    lambda_name: str
    payload: dict
    Returns
    -------
    dict: payload response from a lambda
    Examples
    --------
    >>> from core_aws.lambdas import find_information_by_lambda_async
    >>> find_information_by_lambda_async("client", "lambda_name", "payload")
    """
    if payload is None:
        payload = {
            "pathParameters": {
                "client": client
            }
        }

    response = call_lambda_async(lambda_name, payload)
    LOGGER.info(f'response from lambda {lambda_name}: {response}')
    return response


def update_loan(loan_id, fields_to_update):
    """
    update_loan_table.
    Parameters
    ----------
    loan_id : int
    fields_to_update: dict
    Returns
    -------
    bool: return a bool if the loan table was updated
    Examples
    --------
    >>> from core_utils.lending import update_loan
    >>> update_loan("loan_id", {'fields_to_update': 'value_to_update'})
    """
    try:
        fields_to_update.update({'LastUpdate': str(datetime.datetime.now())})
        key = {'LoanID': int(loan_id)}
        response = update_dynamic_fields_in_dynamo('Loan', key, fields_to_update)
    except Exception as error:
        LOGGER.error(f'error to update Loan: {error}')
        return False

    return response


def delete_item_from_table(table_name, keys_to_delete):
    """
    delete item from a dynamo table.
    Parameters
    ----------
    table_name : str
    keys_to_delete: dict
    Returns
    -------
    bool: return a true if the table item was removed
    Examples
    --------
    >>> from core_aws.lambdas import delete_item_from_table
    >>> delete_item_from_table("table_name", {'key_name': 'key_vale'})
    """
    try:
        table = get_table(table_name)
        response = table.delete_item(Key=keys_to_delete)
        return_value = True
        if 'ResponseMetadata' not in response or response['ResponseMetadata']['HTTPStatusCode'] != 200:
            raise LendingException(f'error to delete information from the table: {table_name}')

    except Exception as error:
        LOGGER.error(f'error to delete item from the table {table_name}: {error}')
        LOGGER.error(f'error to delete the item with the key: {keys_to_delete}')
        return False

    return return_value


def validate_response_dynamo_query(response, complete=False, valid_empty=False, data="Items"):
    """
    get last item from loans array.
    Parameters
    ----------
    response : response from dynamo table
    complete: bool to return all data or not
    valid_empty: bool to validate if the data is empty
    data: str with the key of query response or get response that have the data
    Return
    -------
    data or array of data from dynamo, if the data does not found return None
    Examples
    --------
    >>> from core_utils.lending import validate_response_dynamo_query
    >>> validate_response_dynamo_query(table, {'key': 'value'}, {'ResponseMetadata': {'HTTPStatusCode': 200}, 'Items': []}, [])
    """
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    LOGGER.info(f'Validando {data}.....')
    if status_code != 200 or f'{data}' not in response or (valid_empty is False and len(response[f'{data}']) == 0):
        LOGGER.error(f"error in method validate_response_dynamo_query: status code error StatusCode: {status_code}")
        LOGGER.error("Exception Message in validate_response_dynamo_query [is empty]")
        return None

    if complete is True:
        LOGGER.debug("validate_response_dynamo_query executed successfully %s", response[f'{data}'])
        return response[f'{data}']
    else:
        LOGGER.debug("validate_response_dynamo_query executed successfully %s", response[f'{data}'][0])
        return response[f'{data}'][0]


def find_by_client_by_cell_number(cell_number):
    """
    invoke lambda to
    obtain client information from table client with the MSISDN

    Parameters
    ----------
    cell_number : str

    Returns
    -------
    client information


    Examples
    --------
    >>> from core_utils.lending import find_by_client_by_cell_number
    >>> find_by_client_by_cell_number("0984807373")

    """
    try:
        LOGGER.info('method find_by_client_by_cell_number')
        LOGGER.info(f'key to use in the query of table Client, Msisdn: {cell_number}')
        response_client_items = get_items_by_query_from_dynamo('Client', 'Msisdn-ClientID-index',
                                                               Key('Msisdn').eq(str(cell_number)))
        if not response_client_items:
            LOGGER.error(f"not data found response get_items_by_query_from_dynamo Client: {response_client_items}")
            return None

        if len(response_client_items) > 1:
            LOGGER.warning(f'more than one item was found: {response_client_items}')

        return response_client_items[0]
    except Exception as e:
        LOGGER.exception("Exception parameters in find_by_client_by_idmts [%s]", e)
        return None


def find_by_client_by_idmts(id_mts):
    """
    invoke lambda to
    obtain client information from table client with the ClientIDMTS

    Parameters
    ----------
    id_mts : str

    Returns
    -------
    client information


    Examples
    --------
    >>> from core_utils.lending import find_by_client_by_idmts
    >>> find_by_client_by_idmts("2147")

    """
    try:
        LOGGER.info('method find_by_client_by_idmts')
        LOGGER.info(f'key to use in the query of table Client, ClientIDMTS: {id_mts}')
        response_client_items = get_items_by_query_from_dynamo('Client', 'ClientIDMTS-index',
                                                               Key('ClientIDMTS').eq(str(id_mts)))
        if not response_client_items:
            return None

        if len(response_client_items) > 1:
            LOGGER.warning(f'more than one item was found: {response_client_items}')

        return response_client_items[0]
    except Exception as e:
        LOGGER.exception("Exception parameters in find_by_client_by_idmts [%s]", e)
        return None


def get_inswitch_client(data, is_msisdn):
    """
    invoke lambda to
    obtain client information via MSISDN or ClientIDMTS

    Parameters
    ----------
    data : str
    is_msisdn: bool

    Returns
    -------
    customer information


    Examples
    --------
    >>> from core_utils.lending import get_inswitch_client
    >>> get_inswitch_client("0984807373", False)

    """
    if is_msisdn is True:
        LOGGER.info('is comparison with get_inswitch_client')
        response = get_client_information_by_msisdn(data)
    else:
        LOGGER.info('is comparison with get_client_information_by_client_id')
        response = get_client_information_by_client_id(str(data))

    if response.status_code != 200:
        return None

    return response.json()


def compare_client_data(data, process='Login', is_msisdn=False):
    """
    invoke lambda to
    verify that the MSISDN of the clients is correct and edit if it is not correct and record the change in a table.

    Parameters
    ----------
    process
    data: str
    is_msisdn: Boolean

    Returns
    -------
    info_response = {
        "success": the process was carried out successfully,
        "edited": the client's MSISDN was edited,
        "client": customer data from table client
    }

    the service can receive Msisdn or ClientIDMTS if the string size is greater than 7,
    it automatically detects that it is MSISDN
    Examples
    --------
    >>> from core_utils.lending import compare_client_data
    >>> compare_client_data("0984807373")
    or
    >>> compare_client_data("2147")

    """
    info_response = {
        "success": False,
        "edited": False,
        "client": {},
        "msisdn": "",
        "idmts": ""
    }
    cell_number = ""

    if is_msisdn:
        cell_number = str(data)

    try:
        client_inswitch = get_inswitch_client(data, is_msisdn)

        if client_inswitch is None:
            LOGGER.info({'Error': _CLIENT_INSWITCH_NOT_FOUND})
            return info_response

        if is_msisdn is True:
            idmts = client_inswitch.get('metadata', {}).get('CLIENT_ID')
        else:
            LOGGER.info('Se esta agregando el msisdn de inswitch')
            idmts = list(filter(lambda x: x.get('key') == 'CLIENT_ID', client_inswitch['metadata']))[0].get('value')
            cell_number = list(filter(lambda x: x.get('key') == 'MSISDN', client_inswitch['metadata']))[0].get('value')
            cell_len = len(cell_number)
            if 2 > cell_len > 0:
                cell_number = cell_number[0]
            LOGGER.info(f'Datos cell_number: {cell_number}, idmts: {idmts}')

        if cell_number is None or idmts is None:
            return info_response

        info_response["msisdn"] = cell_number
        idmts = str(idmts)
        client = find_by_client_by_idmts(idmts)
        msisdn = client.get('Msisdn')
        info_response["idmts"] = idmts

        if client is None or msisdn is None:
            LOGGER.info({'Error': _CLIENT_NOT_FOUND})
            return info_response

        if msisdn is not None and msisdn == str(cell_number):
            info_response["client"] = client
            info_response["success"] = True
            return info_response

        table = get_table('Client')

        update_expression = "set #Msisdn = :Msisdn, #LastUpdate = :LastUpdate"

        expression_attribute_values = {
            ':Msisdn': cell_number,
            ':LastUpdate': str(datetime.datetime.now()),
        }

        expression_attribute_names = {
            '#Msisdn': 'Msisdn',
            '#LastUpdate': "LastUpdate",
        }

        response = table.update_item(
            Key={'ClientID': client['ClientID']},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="UPDATED_NEW"
        )

        if 'ResponseMetadata' not in response or response['ResponseMetadata']['HTTPStatusCode'] != 200:
            return info_response

        table = get_table('UpdatedCustomerAccounts')

        new_row = {
            'Id': str(uuid.uuid4()),
            'ClientId': client.get('ClientID'),
            'OldMsisdn': msisdn,
            'NewMsisdn': cell_number,
            'UpdateDate': str(datetime.datetime.now()),
            'Process': process
        }

        response_post = table.put_item(
            Item=new_row
        )

        if 'ResponseMetadata' in response_post and response_post['ResponseMetadata']['HTTPStatusCode'] == 200:
            info_response["success"] = True
            info_response["edited"] = True
            LOGGER.info(info_response)
            return info_response
    except Exception as e:
        LOGGER.error(f"Exception compare client: {e}")
        return info_response

    LOGGER.info(info_response)
    return info_response


def create_row_in_dynamo(table_name, item):
    """
    insert in dynamo table table.
    Parameters
    ----------
    table_name : str
    item: dict
    Returns
    -------
    a boolean, True if insert was success, and False if insert was failure.
    Examples
    --------
    >>> from core_aws.dynamo import create_row_in_dynamo
    >>> create_row_in_dynamo('client_id', 'idempotency_key', 'request_id','transaction_type')
    """
    try:
        table = get_table(table_name)
        dynamo_insert = table.put_item(Item=item)
        if 'ResponseMetadata' not in dynamo_insert and dynamo_insert['ResponseMetadata']['HTTPStatusCode'] != 200:
            LOGGER.info(f'error to create the record in {create_row_in_dynamo}')
            return False

        LOGGER.info(f'insert in {table_name} was successfully, data {item}')
        return True
    except Exception as error:
        LOGGER.info(f'error to create the record in {table_name}')
        LOGGER.error("exception Message [%s]" % error)
        return False


def get_item_from_dynamo(table_name, key):
    """
    insert in dynamo table.
    Parameters
    ----------
    table_name : str
    key: dict
    Returns
    -------
    a boolean, True if insert was success, and False if insert was failure.
    Examples
    --------
    >>> from core_aws.dynamo import get_item_from_dynamo
    >>> get_item_from_dynamo('table_name', {'key': 'value'})
    """
    table = get_table(table_name)

    try:
        item = table.get_item(Key=key)
    except Exception as e:
        LOGGER.error(f"error to get item from dynamo in the table {table_name}: {e}")
        raise LendingException(f'error to get item from dynamo in the table {table_name}: {e}')

    if 'Item' not in item:
        return None
    return item['Item']


def find_offer_by_client(client):
    """
    invoke lambda to
    obtain lending-loan-offers via customer_id

    Parameters
    ----------
    client : str

    Returns
    -------
    Status information


    Examples
    --------
    >>> from core_utils.lending import find_offer_by_client
    >>> find_offer_by_client("15")
    """
    table = get_table('lending-loan-offers')

    try:
        offer = table.get_item(Key={'clientId': str(client)})
    except Exception as e:
        LOGGER.error("Exception parameters in find_offer_by_client [%s]", e)
        return None

    return validate_response_dynamo_query(offer, True, True, "Item")


def find_status_by_id(status):
    """
    invoke lambda to
    obtain Status via status_id

    Parameters
    ----------
    status : str

    Returns
    -------
    Status information


    Examples
    --------
    >>> from core_utils.lending import find_status_by_id
    >>> find_status_by_id("1")
    """
    # Constants
    table = get_table('StatusPreaproved')
    try:
        status = table.get_item(Key={'StatusID': int(status)})
    except Exception as e:
        LOGGER.error("Exception parameters in find_status_by_id [%s]", e)
        return None

    return validate_response_dynamo_query(status, True, True, "Item")


def find_loan_by_client(client_id):
    """
    invoke lambda to
    obtain loan information via ClientID

    Parameters
    ----------
    client_id : str

    Returns
    -------
    Loan information


    Examples
    --------
    >>> from core_utils.lending import find_loan_by_client
    >>> find_loan_by_client("5f606515-8367-4308-808f-daa913005181")
    """
    try:
        response_loan = get_items_by_query_from_dynamo('Loan', 'Client-index', Key('Client').eq(str(client_id)))
    except Exception as e:
        LOGGER.exception(f'error in the method find_loan_by_client: {e}')
        return None

    if not response_loan:
        return []
    return response_loan


def validate_access(client_id, customer_id):
    """
    invoke lambda to
    verify that the MSISDN of the clients is correct and edit
    if it is not correct and record the change in a table.

    Parameters
    ----------
    client_id : str
    customer_id : str
    Returns
    -------
    response = {
        "success": El proceso se ejecuto correctamente
        "error": Detalle del error que cerro el proceso
        "status_preapproved": Status Id lending_loan_offers
        "flow": Flujo al cual se redirecciona el front
        "current_loan": Loan actual, solo si es el caso de un credito que se encuentre en status "IN_PROCESS",
                        "REJECTED"
        "status_app": Estatus de app status lending_loan_offers
        "total_loans": Numero de registros loan asociados al cliente
        "access": Garantiza el acceso al app mediante el boton de juvo
        "is_recurrent": El credito es recurrente si no se tinee por lo menos un credito que se haya dispesado
    }

    This service validates access to the application

    Examples
    --------
    >>> from core_utils.lending import validate_access
    >>> validate_access("5f606515-8367-4308-808f-daa913005181", "210045")
    """

    dashboard = "dashboard"
    on_boarding = "onboarding"
    response = {
        "success": False,
        "error": "",
        "status_preapproved": 0,
        "flow": dashboard,
        "current_loan": None,
        "status_app": "U",
        "total_loans": 0,
        "access": False,
        "is_recurrent": False
    }
    status_pre_disper = {
        "IN_PROCESS": True,
        "REJECTED": True
    }
    status_primary = {
        "IN_PROCESS": True,
        "REJECTED": True,
        "ACTIVE": True,
        "LATE": True,
        "EXPIRED": True
    }

    if client_id is None or customer_id is None:
        LOGGER.error(f"data to validate access is incorrect client_id: {client_id} customer_id: {customer_id}")
        response["error"] = f"data to validate access is incorrect client_id: {client_id} customer_id: {customer_id}"
        return response
    try:

        LOGGER.info("------------------------------------- Section 1 -------------------------------------")

        loans = find_loan_by_client(client_id)

        if loans is None:
            LOGGER.info({'Error': _LOAN_NOT_FOUND})
            return response

        if len(loans) > 0:
            if len(loans) > 1:
                response['access'] = True
                LOGGER.info("approved access in multiple loan")
                response['success'] = True
                response['total_loans'] = len(loans)

                for loan in loans:
                    loan_status = loan.get("Status")
                    # ["IN_PROCESS", "ACTIVE", "CLOSED", "LATE", "EXPIRED", "REJECTED"]:

                    if status_primary.get(loan_status) is not None:
                        response["current_loan"] = loan

                if response["current_loan"] is None:
                    response["current_loan"] = loans[-1]

            else:
                loan = loans[0]
                loan_status = loan.get("Status")
                response['total_loans'] = 1

                if status_pre_disper.get(loan_status) is not None:
                    LOGGER.info({'Success': f'the client has a loan in {loan_status}'})
                    response["flow"] = on_boarding
                else:
                    LOGGER.info("approved access in loan")
                    response["access"] = True

                response["current_loan"] = loans[0]

        else:
            LOGGER.info({'Success': 'The client does not have loans'})
            response["flow"] = on_boarding

        LOGGER.info("------------------------------------- Section 2 -------------------------------------")

        offer = find_offer_by_client(customer_id)

        if offer is None or 'Message' in offer:
            response["error"] = _OFFER_NOT_FOUND
            LOGGER.info({'Error': _OFFER_NOT_FOUND})
            return response

        status_preapproved = offer.get('StatusPreapproved')

        if status_preapproved is not None:
            if status_preapproved == 5:
                status_preapproved = 2
            status = find_status_by_id(status_preapproved)

            if status is None:
                response["error"] = _STATUS_PREPPROVED_NOT_FOUND
                LOGGER.info({'Error': _STATUS_PREPPROVED_NOT_FOUND})
                return response

            status_default = {
                "IN_PROCESS": True,
                "CLOSED": True,
                "REJECTED": True,
            }

            status_current_loan = ''

            if response.get("current_loan") is not None:
                status_current_loan = response.get("current_loan", {}).get("Status")

            if offer.get('statusApp') == 'U' and status.get('Description') == 'Oferta':
                if response.get("flow") == dashboard and status_default.get(status_current_loan) is not None:
                    response["status_preapproved"] = 5
            else:
                LOGGER.info("approved access in offers")
                if response.get("flow") == dashboard and status_default.get(status_current_loan) is not None:
                    response['is_recurrent'] = True
                response["access"] = True
                response["status_app"] = offer.get('statusApp')

            current_sp = response.get("status_preapproved")

            if current_sp != 5:
                response["status_preapproved"] = status_preapproved

            response["success"] = True

    except Exception as e:
        LOGGER.error(e)

    return response


def get_items_by_query_from_dynamo(table_name, index_name, key_condition_expression, filter_condition_expression=None,
                                   scan_index_forward=None):
    """
    get items from dynamo table.
    Parameters
    ----------
    table_name : str
    index_name: str
    key_condition_expression: boto3.dynamodb.conditions Key
    filter_condition_expression: boto3.dynamodb.conditions Att
    scan_index_forward: bool
    Returns
    -------
    a dict if query was success, and None if query was failure.
    Examples
    --------
    >>> from core_aws.dynamo import get_items_by_query_from_dynamo
    >>> get_items_by_query_from_dynamo('table_name', 'index_name', Key('field').eq(field_value), Attr('field').eq(value), False)
    """
    LOGGER.info('method: get_items_by_query_from_dynamo')
    LOGGER.info(f'table_name: {table_name}, index_name: {index_name}')
    table = get_table(table_name)
    query = {"IndexName": index_name, "KeyConditionExpression": key_condition_expression}
    if filter_condition_expression:
        query.update({'FilterExpression': filter_condition_expression})

    if scan_index_forward:
        query.update({'ScanIndexForward': scan_index_forward})

    try:
        rows = []
        response = table.query(**query)
        recursive_query(table, query, response, rows)
    except Exception as error:
        LOGGER.error(f"error to get data from dynamo in the table {table_name} error: {error}")
        LOGGER.error(f'rows count searched in dynamo: {len(rows)}, rows searched in dynamo: {rows}')
        raise LendingException(f'error to get data from dynamo in the table {table_name} error: {error}')

    response_to_validate = {
        'ResponseMetadata': {
            'HTTPStatusCode': 200
        },
        'Items': rows
    }
    validated_response = validate_response_dynamo_query(response_to_validate, True)
    LOGGER.info(f'response information from dynamo: {validated_response}')
    return validated_response


def get_loans_by_client(client):
    """
    get items from dynamo table.
    Parameters
    ----------
    client : str
    Returns
    -------
    a dict if query was success, and None if query was failure.
    Examples
    --------
    >>> from core_aws.dynamo import get_loans_by_client
    >>> get_loans_by_client('client')
    """
    return get_items_by_query_from_dynamo('Loan', 'Client-index', Key('Client').eq(client))


def find_tigo_point_name(idpdv):
    """
                  invoke lambda to
                  get the nearest tigo point name

                  Parameters
                  ----------
                  agent_id : str

                  Returns
                  -------
                  the nearest tigo point name


                  Examples
                  --------
                  >>> from core_utils.lending import find_tigo_point_name
                  >>> find_tigo_point_name("0")
                  """
    _DEFAULT_PTM_NAME = 'al PTM mas cercano'
    table = get_table('TigoAgent')
    try:
        response = table.query(
            IndexName='AgentCode-index',
            KeyConditionExpression=Key('AgentCode').eq(str(idpdv)),
            ScanIndexForward=True
        )
    except ClientError as e:
        LOGGER.info(e)
        return _DEFAULT_PTM_NAME

    if len(response['Items']) == 0:
        return _DEFAULT_PTM_NAME
    else:
        return response['Items'][0]['AgentFantasyName']


def register_new_client_sms(data):
    """
                    invoke lambda to
                    register new item in ClientSMS

                    Parameters
                    ----------
                    data : dict

                    Returns
                    -------
                    True if the item was saved
                    False if the item wasn't saved


                    Examples
                    --------
                    >>> from core_utils.lending import register_new_client_sms
                    >>> register_new_client_sms( {
            "client_id": '2ab9865d-0b9d-4650-a8f9-0d66da06c1a1',
            "max_retries": 5,
            "phone_number": '595961316361',
            "sms_template_id": "1",
        })
                    """
    _REGISTER_NEW_SMS = 'Registering new sms'
    _RECORD_SUCCESSFUL = 'Record has been created successful'
    _RECORD_ERROR = 'Error creating the sms record'
    _DEFAULT_SMS = {"SentDate": 'not sent', "Retries": 0, "SmsStatus": 'Pending', "SmsResponse": 'No error',
                    "SMSID": str(uuid.uuid4()), "ClientId": data.get("client_id"),
                    "CreatedDate": str(datetime.datetime.now()),
                    "PhoneNumber": data.get("phone_number"), "MaxRetries": int(data.get("max_retries")),
                    "SmsTemplateId": data.get("sms_template_id"),
                    "DateToSend": data.get("date_to_send"),
                    "EmitterApp": get_table('SMSTemplates').get_item(Key={'SMSId': data.get("sms_template_id"),
                                                                          'Country': 'PRY'})["Item"].get("EmitterApp")}

    if 'params' in data:
        _DEFAULT_SMS["Params"] = data.get("params")
    table = get_table('ClientSMS')
    LOGGER.info(_REGISTER_NEW_SMS)
    response = table.put_item(
        Item=_DEFAULT_SMS
    )

    if 'ResponseMetadata' in response and response['ResponseMetadata']['HTTPStatusCode'] == 200:
        LOGGER.info(f'{_DEFAULT_SMS} - {_RECORD_SUCCESSFUL}')
        return True
    else:
        LOGGER.info(f'{_DEFAULT_SMS} - {_RECORD_ERROR}')
        return False


def get_movements_from_loan_offers_movements_by_client(client, filter_condition_expression=None):
    """
    get items from dynamo table.
    Parameters
    ----------
    client : str
    filter_condition_expression: boto3.dynamodb.conditions Att
    Returns
    -------
    a dict if query was success, and None if query was failure.
    Examples
    --------
    >>> from core_aws.dynamo import get_movements_from_loan_offers_movements_by_client
    >>> get_movements_from_loan_offers_movements_by_client('client')
    """
    arguments = {
        'table_name': 'LoanOffersMovements',
        'index_name': 'ClientId-index',
        'key_condition_expression': Key('ClientId').eq(str(client))
    }
    if filter_condition_expression:
        arguments.update({'filter_condition_expression': filter_condition_expression})

    return get_items_by_query_from_dynamo(**arguments)


def get_last_loan(loans, all_loans=False):
    """
    get last item from loans array.
    Parameters
    ----------
    loans : array
    all_loans: True
    Return
    -------
    a loan if exist, and None if not exist.
    Examples
    --------
    >>> from core_aws.dynamo import get_last_loan
    >>> get_last_loan([{'Status':'ACTIVE'}], False)
    """
    if not all_loans:
        loans = list(filter(lambda x: x.get('Status') not in ['REJECTED', 'CLOSED'], loans))

    if not loans:
        return None

    loan = sorted(loans, key=lambda x: x['CreatedDate'])[-1]
    LOGGER.info(f'last loan: {loan}')
    return loan


def recursive_query(table, query, response, rows):
    """
    get last item from loans array.
    Parameters
    ----------
    table : table of dynamo
    query: parameters to the method query of the dynamo table
    response: dict with the dynamo query response information
    rows: array with the rows of the query data from dyanmo
    Return
    -------
    array of data information from the dynamo table
    Examples
    --------
    >>> from core_utils.lending import recursive_query
    >>> recursive_query(table, {'key': 'value'}, {'ResponseMetadata': {'HTTPStatusCode': 200}, 'Items': []}, [])
    """
    status_code = response['ResponseMetadata']['HTTPStatusCode']
    if status_code != 200:
        raise LendingException(
            f'recursive_query failed, the responses status_code is different from 200, status_code: {status_code}')
    if response['Items']:
        rows.extend(response['Items'])
    if 'LastEvaluatedKey' in response:
        query.update({'ExclusiveStartKey': response.get('LastEvaluatedKey')})
        table_scan = table.query(**query)
        return recursive_query(table, query, table_scan, rows)
    return rows
