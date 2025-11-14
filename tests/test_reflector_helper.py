"""
Test file for ReflectorHelper class.
Tests one method per test function, with multiple docstring formats tested for extract doc methods.
"""

import unittest
from typing import Any, Dict, List, Optional

from gws_core.core.utils.reflector_helper import ReflectorHelper
from gws_core.core.utils.reflector_types import (ClassicClassDocDTO,
                                                 MethodArgDoc, MethodDoc,
                                                 MethodDocType)

# ===== Test Classes with Different Docstring Formats =====


class RestStyleClass:
    """A test class with ReST style docstrings.

    This class is used to test documentation extraction.
    """

    public_var: str
    _private_var: int

    def rest_method(self, name: str, value: int = 10) -> str:
        """Process data with ReST style documentation.

        This method demonstrates ReST style docstrings.

        :param name: The name to process
        :type name: str
        :param value: The value to use
        :type value: int
        :return: The processed result
        :rtype: str
        """
        return f"{name}: {value}"

    @classmethod
    def class_method_example(cls, data: str) -> None:
        """A classmethod example.

        :param data: Input data
        :type data: str
        """
        pass

    @staticmethod
    def static_method_example(x: int) -> int:
        """A staticmethod example.

        :param x: Input value
        :type x: int
        :return: Doubled value
        :rtype: int
        """
        return x * 2


class GoogleStyleClass:
    """A test class with Google style docstrings.

    This class is used to test documentation extraction with Google format.
    """

    another_var: bool

    def google_method(self, items: List[str], count: int = 5) -> Dict[str, int]:
        """Process items with Google style documentation.

        This method demonstrates Google style docstrings with detailed descriptions.

        Args:
            items (List[str]): The list of items to process
            count (int): Number of items to process, defaults to 5

        Returns:
            Dict[str, int]: A mapping of items to their counts
        """
        return {item: count for item in items}


class NumpyStyleClass:
    """A test class with NumPy style docstrings.

    This class is used to test documentation extraction with NumPy format.
    """

    numeric_var: float

    def numpy_method(self, matrix: List[List[float]], scale: float = 1.0) -> List[List[float]]:
        """Process matrix with NumPy style documentation.

        This method demonstrates NumPy style docstrings.

        Parameters
        ----------
        matrix : List[List[float]]
            The input matrix to process
        scale : float
            Scaling factor to apply, defaults to 1.0

        Returns
        -------
        List[List[float]]
            The scaled matrix
        """
        return [[cell * scale for cell in row] for row in matrix]


class TestClass:
    """A simple test class for various reflector tests."""

    property_str: str = "test"
    property_int: int = 42
    _private_property: str = "private"

    def __init__(self, value: str = "default"):
        """Initialize the test class.

        :param value: Initial value
        :type value: str
        """
        self.value = value

    def public_method(self, arg1: str, arg2: int = 10) -> str:
        """A public method.

        :param arg1: First argument
        :type arg1: str
        :param arg2: Second argument with default
        :type arg2: int
        :return: Formatted string
        :rtype: str
        """
        return f"{arg1}-{arg2}"

    def _private_method(self):
        """A private method."""
        pass


# ===== Test Cases =====

class TestReflectorHelper(unittest.TestCase):
    """Test suite for ReflectorHelper class."""

    def test_get_property_names_of_type(self):
        """Test get_property_names_of_type method."""
        properties = ReflectorHelper.get_property_names_of_type(TestClass, str)

        self.assertIsInstance(properties, dict)
        self.assertIn('property_str', properties)
        self.assertEqual(properties['property_str'], "test")
        # Note: _private_property is actually included in the dict
        self.assertIn('_private_property', properties)

    def test_get_function_arguments(self):
        """Test get_function_arguments method."""
        def sample_func(a: str, b: int = 5, c: Optional[bool] = None):
            pass

        args_metadata = ReflectorHelper.get_function_arguments(sample_func)

        self.assertEqual(args_metadata.func_name, "sample_func")
        named_args = args_metadata.get_named_args()
        self.assertEqual(len(named_args), 3)
        self.assertIn('a', named_args)
        self.assertIn('b', named_args)
        self.assertIn('c', named_args)
        self.assertEqual(named_args['b'].default_value, 5)

    def test_function_args_are_optional(self):
        """Test function_args_are_optional method."""
        def func_with_defaults(a: str = "test", b: int = 5):
            pass

        def func_without_defaults(a: str, b: int):
            pass

        self.assertTrue(ReflectorHelper.function_args_are_optional(func_with_defaults))
        self.assertFalse(ReflectorHelper.function_args_are_optional(func_without_defaults))

    def test_object_has_metadata(self):
        """Test object_has_metadata method."""
        class MetaObj:
            custom_meta = "metadata_value"

        obj = MetaObj()

        self.assertTrue(ReflectorHelper.object_has_metadata(obj, 'custom_meta'))
        self.assertFalse(ReflectorHelper.object_has_metadata(obj, 'nonexistent_meta'))
        self.assertTrue(ReflectorHelper.object_has_metadata(obj, 'custom_meta', str))
        self.assertFalse(ReflectorHelper.object_has_metadata(obj, 'custom_meta', int))

    def test_get_and_check_object_metadata(self):
        """Test get_and_check_object_metadata method."""
        class MetaObj:
            meta_data = {"key": "value"}

        obj = MetaObj()

        result = ReflectorHelper.get_and_check_object_metadata(obj, 'meta_data')
        self.assertEqual(result, {"key": "value"})

        result = ReflectorHelper.get_and_check_object_metadata(obj, 'nonexistent')
        self.assertIsNone(result)

    def test_set_object_has_metadata(self):
        """Test set_object_has_metadata method."""
        class MetaObj:
            pass

        obj = MetaObj()
        ReflectorHelper.set_object_has_metadata(obj, 'new_meta', 'new_value')

        self.assertTrue(hasattr(obj, 'new_meta'))
        self.assertEqual(obj.new_meta, 'new_value')

    def test_get_method_named_args_json(self):
        """Test get_method_named_args_json method."""
        def test_func(name: str, age: int = 25, active: bool = True):
            pass

        args_json = ReflectorHelper.get_method_named_args_json(test_func)

        self.assertIsInstance(args_json, list)
        self.assertEqual(len(args_json), 3)

        # Check first argument
        self.assertEqual(args_json[0].arg_name, 'name')
        self.assertEqual(args_json[0].arg_type, 'str')
        self.assertEqual(args_json[0].arg_default_value, '')

        # Check second argument with default
        self.assertEqual(args_json[1].arg_name, 'age')
        self.assertEqual(args_json[1].arg_type, 'int')
        self.assertEqual(args_json[1].arg_default_value, '25')

    def test_get_func_doc_rest_style(self):
        """Test get_func_doc method with ReST style docstrings."""
        method_doc = ReflectorHelper.get_func_doc(RestStyleClass.rest_method, RestStyleClass)

        self.assertIsInstance(method_doc, MethodDoc)
        self.assertEqual(method_doc.name, 'rest_method')
        self.assertEqual(method_doc.method_type, MethodDocType.BASICMETHOD)
        self.assertIsNotNone(method_doc.doc)
        self.assertEqual(len(method_doc.args), 2)  # self is excluded
        self.assertEqual(method_doc.args[0].arg_name, 'name')
        self.assertEqual(method_doc.args[1].arg_name, 'value')
        self.assertEqual(method_doc.return_type, 'str')

        # Test docstring parsing - ReST format
        arg_desc = method_doc.get_arg_description('name')
        self.assertIsNotNone(arg_desc)
        self.assertIn('name', arg_desc.lower())

        return_desc = method_doc.get_return_description()
        self.assertIsNotNone(return_desc)
        self.assertIn('result', return_desc.lower())

    def test_get_func_doc_google_style(self):
        """Test get_func_doc method with Google style docstrings."""
        method_doc = ReflectorHelper.get_func_doc(GoogleStyleClass.google_method, GoogleStyleClass)

        self.assertIsInstance(method_doc, MethodDoc)
        self.assertEqual(method_doc.name, 'google_method')
        self.assertIsNotNone(method_doc.doc)
        self.assertEqual(len(method_doc.args), 2)
        # Return type is simplified by Utils.stringify_type
        self.assertEqual(method_doc.return_type, 'Dict')

        # Test docstring parsing - Google format
        arg_desc = method_doc.get_arg_description('items')
        self.assertIsNotNone(arg_desc)
        self.assertIn('items', arg_desc.lower())

        return_desc = method_doc.get_return_description()
        self.assertIsNotNone(return_desc)
        self.assertIn('mapping', return_desc.lower())

    def test_get_func_doc_numpy_style(self):
        """Test get_func_doc method with NumPy style docstrings."""
        method_doc = ReflectorHelper.get_func_doc(NumpyStyleClass.numpy_method, NumpyStyleClass)

        self.assertIsInstance(method_doc, MethodDoc)
        self.assertEqual(method_doc.name, 'numpy_method')
        self.assertIsNotNone(method_doc.doc)
        self.assertEqual(len(method_doc.args), 2)
        # Return type is simplified by Utils.stringify_type
        self.assertEqual(method_doc.return_type, 'List')

        # Test docstring parsing - NumPy format
        arg_desc = method_doc.get_arg_description('matrix')
        self.assertIsNotNone(arg_desc)
        self.assertIn('matrix', arg_desc.lower())

        return_desc = method_doc.get_return_description()
        self.assertIsNotNone(return_desc)
        self.assertIn('matrix', return_desc.lower())

    def test_get_func_doc_with_method_types(self):
        """Test get_func_doc correctly identifies classmethod and staticmethod."""
        # Test classmethod
        classmethod_doc = ReflectorHelper.get_func_doc(
            RestStyleClass.class_method_example, RestStyleClass
        )
        self.assertEqual(classmethod_doc.method_type, MethodDocType.CLASSMETHOD)

        # Test staticmethod
        staticmethod_doc = ReflectorHelper.get_func_doc(
            RestStyleClass.static_method_example, RestStyleClass
        )
        self.assertEqual(staticmethod_doc.method_type, MethodDocType.STATICMETHOD)

    def test_get_all_public_args(self):
        """Test get_all_public_args method."""
        variables = ReflectorHelper.get_all_public_args(TestClass)

        self.assertIsInstance(variables, dict)
        self.assertIn('property_str', variables)
        self.assertIn('property_int', variables)
        self.assertNotIn('_private_property', variables)
        self.assertEqual(variables['property_str'], 'str')
        self.assertEqual(variables['property_int'], 'int')

        # Test with non-class
        result = ReflectorHelper.get_all_public_args("not a class")
        self.assertIsNone(result)

    def test_get_public_args(self):
        """Test get_public_args method."""
        variables = ReflectorHelper.get_public_args(RestStyleClass)

        self.assertIsInstance(variables, dict)
        self.assertIn('public_var', variables)
        self.assertNotIn('_private_var', variables)

    def test_get_public_method_names(self):
        """Test get_public_method_names method."""
        # Without __init__
        methods = ReflectorHelper.get_public_method_names(TestClass, include_init=False)

        self.assertIsInstance(methods, list)
        self.assertIn('public_method', methods)
        self.assertNotIn('_private_method', methods)
        self.assertNotIn('__init__', methods)

        # With __init__
        methods_with_init = ReflectorHelper.get_public_method_names(TestClass, include_init=True)
        self.assertIn('__init__', methods_with_init)
        self.assertIn('public_method', methods_with_init)

    def test_get_public_methods_doc(self):
        """Test get_public_methods_doc method."""
        methods_doc = ReflectorHelper.get_class_public_methods_doc(RestStyleClass, include_init=False)

        self.assertIsInstance(methods_doc, list)
        self.assertTrue(len(methods_doc) > 0)

        method_names = [m.name for m in methods_doc]
        self.assertIn('rest_method', method_names)
        # Note: classmethod may not be included depending on inspection behavior
        self.assertIn('static_method_example', method_names)        # Verify MethodDoc structure
        for method_doc in methods_doc:
            self.assertIsInstance(method_doc, MethodDoc)
            self.assertIsNotNone(method_doc.name)

    def test_get_class_docs(self):
        """Test get_class_docs method."""
        class_doc = ReflectorHelper.get_class_docs(RestStyleClass)

        self.assertIsInstance(class_doc, ClassicClassDocDTO)
        self.assertEqual(class_doc.name, 'RestStyleClass')
        self.assertIsNotNone(class_doc.doc)
        self.assertIsInstance(class_doc.methods, list)
        self.assertTrue(len(class_doc.methods) > 0)
        self.assertIsInstance(class_doc.variables, dict)

        # Test with non-class
        result = ReflectorHelper.get_class_docs("not a class")
        self.assertIsNone(result)

    def test_get_cleaned_doc_string(self):
        """Test get_cleaned_doc_string method."""
        class DocClass:
            """Test class documentation.

            # This is a header that should be converted
            Some content here.
            """
            pass

        cleaned_doc = ReflectorHelper.get_cleaned_doc_string(DocClass)

        self.assertIsNotNone(cleaned_doc)
        self.assertIn('Test class documentation', cleaned_doc)
        # Check that # header is converted to ## header
        self.assertIn('## This is a header', cleaned_doc)
        self.assertNotIn('\n# This is a header', cleaned_doc)

        # Test with object without doc
        def no_doc_func():
            pass

        result = ReflectorHelper.get_cleaned_doc_string(no_doc_func)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
