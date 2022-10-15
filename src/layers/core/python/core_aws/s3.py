# -*- coding: utf-8 -*-

import logging
import os

import boto3
from botocore.exceptions import (
    ClientError,
)

__all__ = [
    "upload_file_to_bucket_s3",
    "get_object_key_from_trigger_s3",
    "get_bucket_name_from_trigger_s3",
    "generate_pre_signed_url",
    "get_metadata",
    "get_object"
]

s3 = boto3.client("s3")


def upload_file_to_bucket_s3(*, file_name, bucket, object_name=None):
    """
    Upload a file to a bucket.

    Parameters
    ----------
    file_name : str
    bucket : str
    object_name : str

    Returns
    -------
    False if the file is not found or True else.

    Examples
    --------
    >>> from core_aws.s3 import upload_file_to_bucket_s3
    >>> upload_file_to_bucket_s3(file_name='my-file.txt', bucket='my-bucket')

    """
    if not object_name:
        object_name = os.path.basename(file_name)

    try:
        response = s3.upload_file(file_name, bucket, object_name)
    except ClientError as e:
        logging.error(e)
        return False
    logging.debug(str(response))
    return True


def get_object_key_from_trigger_s3(event):
    """
    Gets object key from an event if this is sending by a trigger s3 event.

    Parameters
    ----------
    event : dict

    Returns
    -------
    Object key.

    Examples
    --------
    >>> from core_aws.s3 import get_object_key_from_trigger_s3
    >>> get_object_key_from_trigger_s3(event={'Records': [{'s3': {'object': {'key': 'my-key'}}}]})

    """

    try:
        name = event["Records"][0]["s3"]["object"]["key"]
    except KeyError:
        return None
    return name


def get_bucket_name_from_trigger_s3(event):
    """
    Gets bucket name from an event if this is sending by a trigger s3 event.

    Parameters
    ----------
    event : dict
        Event from trigger s3.

    Returns
    -------
    Bucket name.

    Examples
    --------
    >>> from core_aws.s3 import get_bucket_name_from_trigger_s3
    >>> get_bucket_name_from_trigger_s3(event={'Records': [{'s3': {'bucket': {'name': 'my-bucket'}}}]})

    """
    try:
        bucket = event["Records"][0]["s3"]["bucket"]["name"]
    except KeyError:
        return None
    return bucket


def generate_pre_signed_url(*, bucket, object_key, in_line=False, expiration=3600):
    """
    Generate pre-signed url for an object in a bucket.

    Parameters
    ----------
    bucket : str
        Bucket name where the object is stored.
    object_key : str
        Key of the object.
    in_line: bool

    expiration : int
        Expiration time in seconds. Default is 1 hour.

    Returns
    -------
    A pre-signed url.

    Examples
    --------
    >>> from core_aws.s3 import generate_pre_signed_url
    >>> generate_pre_signed_url(bucket='my-bucket', object_key='my-key')

    """
    parameters = {"Bucket": bucket, "Key": object_key}
    if in_line:
        parameters.update({"ResponseContentDisposition": "inline"})

    response = s3.generate_presigned_url(
        "get_object", Params=parameters, ExpiresIn=expiration
    )
    return response


def get_metadata(*, bucket: str, key: str, default=None):
    """Get metadata from an s3 object.

    Request an object from s3 and return get the metadata if it not found return default value.

    Parameters
    ----------
    bucket : str
        Bucket name where the object is stored.
    key : str
        Key of the object.
    default : any
        Default value to return if the object metadata is not found.

    Returns
    -------
    An object metadata or default value.

    Examples
    --------
    >>> from core_aws.s3 import get_metadata
    >>> get_metadata(bucket='my-bucket', key='my-key')

    """
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj.get("Metadata", default)


def get_object(*, bucket: str, key: str):
    """Get metadata from an s3 object.

    Request an object from s3 and return get the metadata if it not found return default value.

    Parameters
    ----------
    bucket : str
        Bucket name where the object is stored.
    key : str
        Key of the object.

    Returns
    -------
    An object or default value.

    Examples
    --------
    >>> from core_aws.s3 import get_object
    >>> get_object(bucket='my-bucket', key='my-key')

    """
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj
