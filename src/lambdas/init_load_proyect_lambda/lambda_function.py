import boto3
import json
from core_api.responses import api_response
from core_utils.utils import get_logger

LOGGER = get_logger("init_load_proyect_lambda")


def lambda_handler(event, context):
    try:
        headers = event.get('headers')
        client = boto3.resource(headers['client'])
        table = client.Table(headers['table'])

        # client = boto3.resource("dynamodb")
        # table = client.Table("suscribers")

        LOGGER.info({'client: ': headers['client']})
        LOGGER.info({'table: ': headers['table']})

        suscribers = table.scan()['Items']
        suscribers_list = ""

        for suscriber in suscribers:
            suscribers_list += "{Valor: " + suscriber["name"] + "},"

    except Exception as err:
        return api_response(f"Unexpected {err=}, {type(err)=}", 200)

    return api_response(suscribers_list, 200)
