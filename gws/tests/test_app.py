import sys
import os
import unittest

import asyncio

from peewee import CharField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource, Process
from gws.prism.view import HTMLView, JSONView
from gws.prism.controller import Controller


class PersonHTMLView(HTMLView):
    name = 'gws.test.person-html-view'
    content = "<b>Postion:<b>{{view.model.data['position']}}<b>Weight:<b>{{view.model.data['weigth']}}"

class PersonJSONView(HTMLView):
    name = 'gws.test.person-json-view'
    content = '{"position":"{{view.model.data["position"]}}", "weight":"{{view.model.data["weigth"]}}"}'

class Person(Resource):
    view_types = {
        PersonHTMLView.name: PersonHTMLView, 
        PersonJSONView.name: PersonJSONView 
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.data = { 
            "position": 0,
            "weight": 70
        }
    
    @property
    def position(self):
        return self.data['position']

    @property
    def weight(self):
        return self.data['weight']

    def set_position(self, val):
        self.data['position'] = val

    def set_weight(self, val):
        self.data['weight'] = val

class Move(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Moving")
        p = Person()
        p.set_position(self._input['person'].position + params['moving_step'])
        p.set_weight(self._input['person'].weight)
        self.output['person'] = p

class Eat(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Eating")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight + params['food_weight'])
        self.output['person'] = p

class Wait(Process):
    input_specs = {'person' : Person}
    output_specs = {'person' : Person}
    async def task(self, params={}):
        print("Waiting")
        p = Person()
        p.set_position(self.input['person'].position)
        p.set_weight(self.input['person'].weight)
        self.output['person'] = p
        await asyncio.sleep(.5) #wait for .5 sec

class TestApp(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
   
    def test_view(self):
        elon = Person()
        html_view = PersonHTMLView(elon)
        json_view = PersonJSONView(elon)
        elon.name = 'Elon Musk'

        # we suppose that the request comes from the view
        async def app(scope, receive, send):
            request = Request(scope, receive)
            html = await App.ctrl.action(request)
            response = HTMLResponse(html)
            await response(scope, receive, send)

        client = TestClient(app)
        params = """{
            "name" : "person_html_view",
            "params":{
                "name" : "Elon Musk"
            }
        }"""

        # Test update_view => html
        params = """{ "job" : "engineer" }"""
        response = client.get('/?action=update_view&uri='+html_view.uri+'&params=' + str(params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "Model="+elon.uuid+" & View URI="+html_view.uri+": I am <b>Elon Musk</b>! My job is engineer.")
        print(response.content)
