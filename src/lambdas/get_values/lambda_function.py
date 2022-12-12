from core_api.responses import api_response


def lambda_handler(event, _):
    headers = event.get('headers')
    response_valor = headers['valor']
    return api_response(response_valor, 200)
