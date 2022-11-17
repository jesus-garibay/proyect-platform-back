import boto3
import json


def lambda_handler(event, context):
    client = boto3.resource("dynamodb")
    table = client.Table("suscribers")

    suscribers = table.scan()['Items']
    suscribers_list = ""

    for suscriber in suscribers:
        suscribers_list += suscriber["name"] + " "

    print("""{'statusCode': 200,
        'body': json.dumps(suscribers_list),
        'headers': {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
        }""")

    return {
        'statusCode': 200,
        # 'body': json.dumps('Hello from Lambda!')
        'body': json.dumps(suscribers_list),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }
