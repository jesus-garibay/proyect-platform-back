from core_api.responses import api_response


def lambda_handler(event, context):
    print(event)
    return api_response('Hello world', 200)
