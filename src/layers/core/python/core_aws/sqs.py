import json
from typing import Dict, Any, List

import boto3
from core_aws.ssm import get_parameter
from core_utils.utils import get_logger

__all__ = [
    "send_message",
    "send_message_attributes_automatic",
    "get_type_data",
    "parse_event",
    "get_queue_by_name",
    "is_queue_empty"
]
LAYER_NAME = "layer-sqs"
LOGGER = get_logger(LAYER_NAME)

SQS_PARAMETERS = get_parameter('Queues', use_environ=True)
SQS_NAMES = SQS_PARAMETERS.get('queue_names', {})

sqs_client = boto3.client('sqs')
sqs_resource = boto3.resource('sqs')


def send_message(data, sqs_name, message_attributes, delay_seconds=0, message_group_id=None):
    """
        Get a parameter from SQS service on aws.

        Parameters
        ----------
        data : Diccionario
        sqs_name : str
            name SQS url
        message_attributes : Diccionario
        delay_seconds : int
        message_group_id: str
        Returns
        -------
        str
            The value MessageId or SQS not executed.


        Examples
        --------
        >>> from core_aws.sqs import send_message
        >>> send_message("/my/parameter")

        """
    if sqs_name is None or data is None or message_attributes is None:
        return "incorrect data"
    try:
        url = SQS_PARAMETERS.get(sqs_name)
        if url is None:
            return "incorrect data"

        if message_group_id is not None:
            response_sqs = sqs_client.send_message(
                QueueUrl=url,
                DelaySeconds=delay_seconds,
                MessageAttributes=message_attributes,
                MessageBody=(json.dumps(data)),
                MessageGroupId=message_group_id
            )
        else:
            response_sqs = sqs_client.send_message(
                QueueUrl=url,
                DelaySeconds=delay_seconds,
                MessageAttributes=message_attributes,
                MessageBody=(json.dumps(data))
            )
        return response_sqs['MessageId']
    except Exception as error:
        LOGGER.error(f'SQS not executed: {error}')
        return "SQS not executed"


def send_message_attributes_automatic(data, sqs_name, delay_seconds=0):
    """
        Get a parameter from SQS service on aws.

        Parameters
        ----------
        data : Diccionario
        sqs_name : str
            name SQS url
        delay_seconds : int

        Returns
        -------
        str
            The value MessageId or SQS not executed.


        Examples
        --------
        >>> from core_aws.sqs import send_message
        >>> send_message("/my/parameter")

        """
    if sqs_name is None or data is None:
        return "incorrect data"

    url = SQS_PARAMETERS.get(sqs_name)
    if url is None:
        return "incorrect data"

    size_message = len(data)
    key_message = list(data.keys())
    info_message = list(data.values())
    message_attributes = {}

    for index in range(size_message):
        message_attributes[key_message[index]] = {
            'DataType': get_type_data(info_message[index]),
            'StringValue': str(info_message[index])
        }
    LOGGER.info(message_attributes)
    try:
        response_sqs = sqs_client.send_message(
            QueueUrl=url,
            DelaySeconds=delay_seconds,
            MessageAttributes=message_attributes,
            MessageBody=(json.dumps(data))
        )
        return response_sqs['MessageId']
    except Exception as error:
        LOGGER.error(f'SQS not executed: {error}')
        return "SQS not executed"


def get_type_data(data):
    """
        Take a event from lambda input and return only the data that will be used in the process.
        Parameters
        ----------
        data : Diccionario
        Returns
        -------
        str
            The value MessageId or SQS not executed.


        Examples
        --------
        >>> from core_aws.sqs import get_type_data
        >>> get_type_data(data)

        """
    type_data = {
        "<class 'int'>": "Number",
        "<class 'float'>": "Number",
        "<class 'str'>": "String",
    }
    type_result = type_data.get(str(type(data)))
    if type_result is None:
        type_result = "String"

    return type_result


def parse_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
        Take a event from lambda input and return only the data that will be used in the process.
        Parameters
        ----------
        event : Diccionario
        Returns
        -------
        str
            The value MessageId or SQS not executed.
        Examples
        --------
        >>> from core_aws.sqs import parse_event
        >>> parse_event({'Records': [{}]})

        """
    try:
        records = event['Records']
    except KeyError:
        raise ValueError('The event not contain the key "Records"')
    if not isinstance(records, list):
        raise TypeError(f"The records should be a list type object not a {type(records)}")
    return records


def get_queue_by_name(queue_name):
    """
        Get a sqs from aws.
        Parameters
        ----------
        queue_name : str
            name SQS

        Returns
        -------
        sqs.Queue
            The instance of sqs by name.
        Examples
        --------
        >>> from core_aws.sqs import get_queue_by_name
        >>> get_queue_by_name("sqs_name")
    """
    queue = sqs_resource.get_queue_by_name(QueueName=queue_name)

    if not queue:
        return None

    return queue


def is_queue_empty(queue_name):
    """
        Get a count sqs messages from aws.
        Parameters
        ----------
        queue_name : str
            name SQS

        Returns
        -------
        bool
            The True if the queue has not message.
        Examples
        --------
        >>> from core_aws.sqs import is_queue_empty
        >>> is_queue_empty("sqs_name")
    """
    queue_name = SQS_NAMES.get(queue_name)

    if not queue_name:
        raise SQSException(f'error to get queue_name from parameter store, queue_name: {queue_name}')
    queue = get_queue_by_name(queue_name)

    if not queue:
        return None

    LOGGER.info(f'queue data: {queue}')
    messages_delayed = queue.attributes.get("ApproximateNumberOfMessagesDelayed")
    messages_not_visible = queue.attributes.get("ApproximateNumberOfMessagesNotVisible")
    messages = queue.attributes.get("ApproximateNumberOfMessages")
    LOGGER.info(f'ApproximateNumberOfMessagesDelayed: {messages_delayed}')
    LOGGER.info(f'ApproximateNumberOfMessagesNotVisible: {messages_not_visible}')
    LOGGER.info(f'ApproximateNumberOfMessages: {messages}')

    total_messages = int(messages_delayed) + int(messages_not_visible) + int(messages)
    return total_messages == 0


class SQSException(Exception):
    def __init__(self, message):
        super().__init__(message)
