import sys
import os
import unittest

import asyncio

from peewee import CharField, ForeignKeyField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource, Process, ResourceViewModel
from gws.prism.view import HTMLViewTemplate, JSONViewTemplate
from gws.prism.controller import Controller


# ##############################################################################
#
# Class definition
#
# ##############################################################################


class Person(Resource):
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

class PersonHTMLViewModel(ResourceViewModel):
    template = HTMLViewTemplate("Model={{view_model.model.id}} & View URI={{view_model.uri}}: I am <b>{{view_model.model.name}}</b>! My job is {{view_model.data.job}}.")

class PersonJSONViewModel(ResourceViewModel):
    template = JSONViewTemplate('{"model_id":"{{view_model.model.id}}", "view_uri":"{{view_model.uri}}", "name": "{{view_model.model.name}}!", "job":"{{view_model.data.job}}"}')

Person.register_view_models([
    PersonHTMLViewModel, 
    PersonJSONViewModel
])

Controller.register_models([
    Person, 
    PersonHTMLViewModel, 
    PersonJSONViewModel
])

# ##############################################################################
#
# Testing
#
# ##############################################################################


class TestApp(unittest.TestCase):
    
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
        elon_vmodel = PersonHTMLViewModel(elon)
        elon.set_name('Elon Musk')

        Controller.save_all()

        # we suppose that the request comes from the view
        async def app(scope, receive, send):
            request = Request(scope, receive)
            vm = await App.ctrl.action(request)
            html = vm.render()
            response = HTMLResponse(html)
            await response(scope, receive, send)

        Controller.is_query_params = True
        client = TestClient(app)

        # Test update_view => html
        params = """{ "job" : "engineer" }"""
        response = client.get(Controller.build_url(
            action = "view", 
            uri_name = elon_vmodel.uri_name,
            uri_id = elon_vmodel.uri_id,
            params = str(params)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "Model="+str(elon.id)+" & View URI="+elon_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")
        print(response.content)

    def test_app(self):
        Controller.is_query_params = False
        app = App()
        app.start()