from typing import Dict
from unittest import TestCase

from starlette.exceptions import HTTPException

from gws_core import BadRequestException, ExceptionHandler, ExceptionResponse


# test_exception
class TestException(TestCase):
    """File to test exception and exception handler. It is important to test the exception handler
    because if an exception happens in it, it would be bad

    :param BaseTestCase: [description]
    :type BaseTestCase: [type]
    """

    def test_exception_detail(self):
        """Test a BadRequestException with  detail args"""
        exception = BadRequestException(detail="Error {{message}}", detail_args={"message": "test"})
        self.assertIsNotNone(exception.instance_id)
        self.assertEqual(exception.get_detail_with_args(), "Error test")

    def test_handle_know_exception(self):
        """Test handling a BaseHTTPException"""
        try:
            raise BadRequestException(detail="Error", unique_code="known_exception")
        except BadRequestException as err:
            response: ExceptionResponse = ExceptionHandler.handle_exception(
                request=None, exception=err
            )
            self.assertEqual(response.status_code, 400)
            body: Dict = response.get_json_body()
            self.assertEqual(body["code"], "test_gws_core.known_exception")
            self.assertEqual(body["detail"], "Error")
            self.assertEqual(body["instanceId"], err.instance_id)

    def test_http_exception(self):
        """Test handling a http exception"""
        try:
            raise HTTPException(detail="Error", status_code=400)
        except HTTPException as err:
            response: ExceptionResponse = ExceptionHandler.handle_exception(
                request=None, exception=err
            )
            self.assertEqual(response.status_code, 400)
            body: Dict = response.get_json_body()
            self.assertEqual(body["code"], "test_gws_core.test_exception.py.test_http_exception")
            self.assertEqual(body["detail"], "Error")
            self.assertIsNotNone(body["instanceId"])

    def test_unknown_exception(self):
        """Test handling a unkonwn exception"""
        try:
            raise Exception("Error")
        except Exception as err:
            response: ExceptionResponse = ExceptionHandler.handle_exception(
                request=None, exception=err
            )
            self.assertEqual(response.status_code, 500)
            body: Dict = response.get_json_body()
            self.assertEqual(body["code"], "test_gws_core.test_exception.py.test_unknown_exception")
            self.assertEqual(body["detail"], "Error")
            self.assertIsNotNone(body["instanceId"])
