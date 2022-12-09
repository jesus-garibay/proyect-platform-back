from unittest import TestCase
from .lambda_function import lambda_handler
from core_utils.decorators import ignore_warnings
from core_api.utils import get_status_code, get_body
from core_utils.utils import get_logger

LOGGER = get_logger("init_load_proyect_lambda")


class TestLambda(TestCase):
    def setUp(self) -> None:
        self.event = {
            "headers": {
                "client": "dynamodb",
                "table": "suscribers"
            }

        }

    @ignore_warnings
    def test_lambda_handler(self):
        # result = lambda_handler(self.event, None)
        # status_code = get_status_code(result)
        # self.assertEqual(200, status_code)
        result = lambda_handler(self.event, None)
        self.__generic_test_save_get_client_information(result, 200)

    def __generic_test_save_get_client_information(self, result, expected_code):
        status_code = get_status_code(result)
        body = get_body(result)
        LOGGER.info(body)
        self.assertEqual(expected_code, status_code)
