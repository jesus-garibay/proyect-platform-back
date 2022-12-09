from core_api.responses import api_response


def lambda_handler(event, context):
    return api_response('Hello world', 200)
