import boto3
import json
from core_api.responses import api_response
from core_utils.utils import get_logger

LOGGER = get_logger("")
def lambda_handler(event, context):
    client = boto3.resource("dynamodb")
    table = client.Table("suscribers")

    suscribers = table.scan()['Items']
    suscribers_list = ""

    for suscriber in suscribers:
        suscribers_list += suscriber["name"] + " "

    # print("""{'statusCode': 200,
    #     'body': json.dumps(suscribers_list),
    #     'headers': {
    #     'Content-Type': 'application/json',
    #     'Access-Control-Allow-Origin': '*'
    #     }""")
    return api_response(suscribers_list, 200)
    # return {
    #     'statusCode': 200,
    #     # 'body': json.dumps('Hello from Lambda!')
    #     'body': json.dumps(suscribers_list),
    #     'headers': {
    #         'Content-Type': 'application/json',
    #         'Access-Control-Allow-Origin': '*'
    #     },
    # }
