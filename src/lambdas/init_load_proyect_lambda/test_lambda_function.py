from unittest import TestCase
from core_api.utils import get_status_code
from .lambda_function import lambda_handler
from core_utils.decorators import ignore_warnings

class TestLambda(TestCase):
    def setUp(self) -> None:
        self.event = {
                      "key1": "value1",
                      "key2": "value2",
                      "key3": "value3"
                    }

    @ignore_warnings
    def test_lambda_handler(self):
        result = lambda_handler(self.event, None)
        status_code = get_status_code(result)
        self.assertEqual(200, status_code)
