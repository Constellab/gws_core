
import unittest
import copy

from peewee import CharField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource, ViewModel
from gws.prism.view import HTMLViewTemplate, JSONViewTemplate

from gws.prism.controller import Controller

from peewee import ForeignKeyField

class Person(Resource):
    name = CharField(null=True)

class PersonHTMLViewModel(ViewModel):
    name = 'gws.test.person-html-view'
    template = HTMLViewTemplate("I am <b>{{view_model.model.name}}</b>! My job is {{view_model.data.job}}.")
    model = ForeignKeyField(Person, backref='view_model')

class PersonJSONViewModel(ViewModel):
    name = 'person-json-view'
    template = JSONViewTemplate('{"name": "{{view_model.model.name}}!", "job":"{{view_model.data.job}}"}')
    model = ForeignKeyField(Person, backref='view_model')

Controller.register_models([Person, PersonHTMLViewModel, PersonJSONViewModel])

class TestHTMLView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        Person.drop_table()
        pass
    
    def test_view(self):
        elon = Person()
        view_model = PersonHTMLViewModel(elon)
        self.assertEqual(view_model.data, {})

        elon.name = 'Elon Musk'
        params = {"job" : "engineer"}
        html = view_model.render(params)
        print(html)

        self.assertEqual(html, "I am <b>Elon Musk</b>! My job is engineer.")
        self.assertEqual(view_model.data, params)
        self.assertEqual(view_model.data, params)
        self.assertEqual(len(Controller.models), 2)

        self.assertTrue( view_model.model is elon )
        self.assertTrue( view_model.id is None )
        self.assertTrue( elon.id is None )
        
class TestJSONView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass
    
    def test_view(self):
        elon = Person()
        view_model = PersonJSONViewModel(elon)
        elon.name = 'Elon Musk'

        params = {"job" : "engineer"}
        json_text = view_model.render(params)
        print(json_text)

        self.assertEqual(json_text, '{"name": "Elon Musk!", "job":"engineer"}')
        self.assertEqual(view_model.data, params)
        self.assertEqual(view_model.data, params)
        self.assertEqual(len(Controller.models), 4)
        self.assertEqual(view_model.model.id, None)
        self.assertEqual(view_model.id, None)

        view_model.save()     #save the model and view_model
        
        self.assertTrue(isinstance(view_model.model.id, int))
        self.assertTrue(isinstance(view_model.id, int))

        # retrieve the view_model
        vmodel2 = PersonJSONViewModel.get( PersonJSONViewModel.id == view_model.id )
        self.assertEqual(vmodel2.id, view_model.id)
        self.assertEqual(vmodel2.model.id, view_model.model.id)

        # print("-----")
        # print(vmodel2.model.id)
