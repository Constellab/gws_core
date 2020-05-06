
import unittest
import copy
import json

from peewee import CharField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource
from gws.prism.view import HTMLView, JSONView
from gws.prism.controller import Controller


class PersonHTMLView(HTMLView):
    name = 'gws.test.person-html-view'
    content = "Model={{view.model.uuid}} & View URI={{view.uri}}: I am <b>{{view.model.name}}</b>! My job is {{params.job}}."

class PersonJSONView(HTMLView):
    name = 'gws.test.person-json-view'
    content = '{"model_id":"{{view.model.uuid}}", "view_uri":"{{view.uri}}", "name": "{{view.model.name}}!", "job":"{{params.job}}"}'

class Person(Model):
    name = CharField()
    view_types = {
        PersonHTMLView.name: PersonHTMLView, 
        PersonJSONView.name: PersonJSONView 
    }

class TestController(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass
    
    def test_controller(self):
        elon = Person()
        html_view = PersonHTMLView(elon)
        json_view = PersonJSONView(elon)
        elon.name = 'Elon Musk'
        
        Controller.register(html_view)

        self.assertEqual(Controller.get_view(html_view.uri), html_view)

        # we suppose that the request comes from the view
        # url = "/action/{uri}/{params}",
        async def app(scope, receive, send):
            request = Request(scope, receive)
            html = await Controller.action(request)
            response = HTMLResponse(html)
            await response(scope, receive, send)

        client = TestClient(app)

        # Test update_view => html
        params = """{ "job" : "engineer" }"""
        response = client.get('/?action=update_view&uri='+html_view.uri+'&params=' + str(params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "Model="+elon.uuid+" & View URI="+html_view.uri+": I am <b>Elon Musk</b>! My job is engineer.")
        print(response.content)

        # Test update_view => json
        params = """{ "job" : "engineer" }"""
        response = client.get('/?action=update_view&uri='+json_view.uri+'&params=' + str(params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+elon.uuid+'", "view_uri":"'+json_view.uri+'", "name": "Elon Musk!", "job":"engineer"}')
        print(response.content)

        # Test update_view different params => json
        params = """{ "job" : "Tesla Maker" }"""
        response = client.get('/?action=update_view&uri='+json_view.uri+'&params=' + str(params))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+elon.uuid+'", "view_uri":"'+json_view.uri+'", "name": "Elon Musk!", "job":"Tesla Maker"}')
        print(response.content)
        
        # Test create_view => json
        params = """{
            "view":"gws.test.person-json-view", 
            "params":{
                "job" : "SpaceX CEO"
            } 
        }"""
        response = client.get('/?action=create_view&uri='+html_view.uri+'&params=' + str(params))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.decode("utf-8"), '{"model_id":"'+elon.uuid+'", "view_uri":"'+json_view.uri+'", "name": "Elon Musk!", "job":"SpaceX CEO"}')
        
        json_response = json.loads(response.content.decode("utf-8"))
        new_uri = json_response["view_uri"]
        new_json_view = Controller.get_view(new_uri)
        self.assertEqual(type(new_json_view), PersonJSONView)
        self.assertFalse(new_json_view is json_view)
        self.assertEqual(new_json_view.model, elon)
        print(response.content)



