
import unittest
import copy

from peewee import CharField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource
from gws.prism.view import HTMLView, JSONView


class PersonHTMLView(HTMLView):
    name = 'gws.test.person-html-view'
    content = "I am <b>{{view.model.name}}</b>! My job is {{params.job}}."

class PersonJSONView(HTMLView):
    name = 'person-json-view'
    content = '{"name": "{{view.model.name}}!", "job":"{{params.job}}"}'

class Person(Model):
    name = CharField()
    view_types = {
        PersonHTMLView.name: PersonHTMLView, 
        PersonJSONView.name: PersonJSONView 
    }
    
class TestHTMLView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_view(self):
        elon = Person()
        view = PersonHTMLView(elon)

        full_params = {'params': {}, '__meta__': {'view_class': 'PersonHTMLView', 'model_id': None}}
        self.assertEqual(view.view_model.params, {})
        self.assertEqual(view.view_model.data, full_params)

        elon.name = 'Elon Musk'
        params = {"job" : "engineer"}
        html = view.render(params)
        print(html)

        self.assertEqual(html, "I am <b>Elon Musk</b>! My job is engineer.")
        self.assertEqual(view.params, params)

        full_params = {'params': params, '__meta__': {'view_class': 'PersonHTMLView', 'model_id': None}}
        self.assertEqual(view.view_model.params, params)
        self.assertEqual(view.view_model.data, full_params)

class TestJSONView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_view(self):
        elon = Person()
        view = PersonJSONView(elon)
        elon.name = 'Elon Musk'

        params = {"job" : "engineer"}
        json_text = view.render(params)
        print(json_text)

        self.assertEqual(json_text, '{"name": "Elon Musk!", "job":"engineer"}')
        self.assertEqual(view.params, params)

        full_params = {'params': params, '__meta__': {'view_class': 'PersonJSONView', 'model_id': None}}
        self.assertEqual(view.view_model.params, params)
        self.assertEqual(view.view_model.data, full_params)
