from unittest import TestCase
from .lambda_function import lambda_handler
from core_api.utils import get_status_code, get_body
from core_utils.utils import get_logger

LOGGER = get_logger("get_values")


class TestLambda(TestCase):
    def setUp(self) -> None:
        self.event = {
            "headers": {
                "valor": "Hello Gary8"
            }
        }

    def test_lambda_handler(self):
        result = lambda_handler(self.event, None)
        self.__generic_test(result, 200)

    def __generic_test(self, result, expected_code):
        status_code = get_status_code(result)
        body = get_body(result)
        LOGGER.info(body)
        self.assertEqual(expected_code, status_code)
