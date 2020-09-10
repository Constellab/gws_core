import sys
import os
import unittest

import asyncio

from peewee import CharField, ForeignKeyField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.app import App
from gws.prism.model import Model, Resource, Process, HTMLViewModel, JSONViewModel
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

class HTMLPersonViewModel(HTMLViewModel):
    model_specs = [ Person ]
    template = HTMLViewTemplate("Model={{vmodel.model.id}} & View URI={{vmodel.uri}}: I am <b>{{vmodel.model.name}}</b>! My job is {{vmodel.data.job}}.")

class JSONPersonViewModel(JSONViewModel):
    model_specs = [ Person ]
    template = JSONViewTemplate('{"model_id":"{{vmodel.model.id}}", "view_uri":"{{vmodel.uri}}", "name": "{{vmodel.model.name}}!", "job":"{{vmodel.data.job}}"}')

# Person.register_view_model_specs([
#     HTMLPersonViewModel, 
#     JSONPersonViewModel
# ])

# ##############################################################################
#
# Testing
#
# ##############################################################################


class TestApp(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass
   
    def test_view(self):
        elon = Person()
        elon_vmodel = HTMLPersonViewModel(elon)
        elon.set_name('Elon Musk')

        elon.save()
        elon_vmodel.save()

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
        params = """{"vdata": { "job" : "engineer" }}"""
        response = client.get(Controller.build_url(
            action = "read", 
            uri = elon_vmodel.uri,
            data = str(params)
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.content.decode("utf-8"), 
            "Model="+str(elon.id)+" & View URI="+elon_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer."
        )
        print(response.content)