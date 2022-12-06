from unittest import TestCase
from .lambda_function import lambda_handler
from core_utils.decorators import ignore_warnings
from core_api.utils import get_status_code, get_body
from core_utils.utils import get_logger

LOGGER = get_logger("")


class TestLambda(TestCase):
    def setUp(self) -> None:
        self.event = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
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
