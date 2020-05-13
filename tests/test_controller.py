
import unittest
import copy
import json

from peewee import CharField, ForeignKeyField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from gws.prism.app import App
from gws.prism.model import Model, Resource, ResourceViewModel
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

class TestControllerHTTP(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.create_table()
        PersonHTMLViewModel.create_table()
        PersonJSONViewModel.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass
    
    def test_controller(self):
        print("")
        print("# HTTP Testing")
        print("# -----------------")

        elon = Person()
        elon_vmodel = PersonHTMLViewModel(elon)
        json_vmodel = PersonJSONViewModel(elon)
        elon.set_name('Elon Musk')
        
        Controller.save_all()

        self.assertEqual( Controller.fetch_model(elon_vmodel.uri), elon_vmodel )

        # assert that local import does not affect class
        from gws.prism.controller import Controller as Ctrl
        self.assertEqual(Ctrl.fetch_model(elon_vmodel.uri), elon_vmodel)

        self.assertEqual(Ctrl.models, Controller.models)

        # we suppose that the request comes from the view
        # url = "/action/{uri}/{params}",
        async def app(scope, receive, send):
            assert scope['type'] == 'http'
            request = Request(scope, receive)
            vm = await Controller.action(request)
            html = vm.render()
            response = HTMLResponse(html)
            await response(scope, receive, send)

        Controller.is_query_params = True
        client = TestClient(app)

        # Test update_view => html
        params = """{ "job" : "engineer" }"""
        response = client.get(Controller.build_url(
            action = 'update_view', 
            uri_name = elon_vmodel.uri_name,
            uri_id = elon_vmodel.uri_id,
            params = params
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "Model="+str(elon.id)+" & View URI="+elon_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")
        print(response.content)

        # Test update_view => json
        params = """{ "job" : "engineer" }"""
        response = client.get(Controller.build_url(
            action = 'update_view', 
            uri_name = json_vmodel.uri_name,
            uri_id = json_vmodel.uri_id,
            params = params
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"engineer"}')
        print(response.content)

        # Test update_view different params => json
        params = """{ "job" : "Tesla Maker" }"""
        response = client.get(Controller.build_url(
            action = 'update_view', 
            uri_name = json_vmodel.uri_name,
            uri_id = json_vmodel.uri_id,
            params = params
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"Tesla Maker"}')
        print(response.content)
        
        # Test create_view => json
        params = """{
            "view":"tests-test-controller-personjsonviewmodel", 
            "params":{
                "job" : "SpaceX CEO"
            } 
        }"""

        response = client.get(Controller.build_url(
            action = 'create_view', 
            uri_name = elon_vmodel.uri_name,
            uri_id = elon_vmodel.uri_id,
            params = params
        ))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"SpaceX CEO"}')
        json_response = json.loads(response.content.decode("utf-8"))
        new_uri = json_response["view_uri"]
        new_json_view = Controller.fetch_model(new_uri)
        self.assertEqual(type(new_json_view), PersonJSONViewModel)
        self.assertFalse(new_json_view is json_vmodel)
        self.assertEqual(new_json_view.model, elon)
        print(response.content)

class TestControllerWebSocket(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.create_table()
        PersonHTMLViewModel.create_table()
        PersonJSONViewModel.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass
    
    def test_controller(self):
        print("")
        print("# WebSocket Testing")
        print("# -----------------")

        elon = Person()
        elon_vmodel = PersonHTMLViewModel(elon)
        elon.set_name('Elon Musk')
        
        Controller.save_all()

        self.assertEqual(Controller.fetch_model(elon_vmodel.uri), elon_vmodel)

        # we suppose that the request comes from the view
        # url = "/action/{uri}/{params}",
        async def app(scope, receive, send):
            assert scope['type'] == 'websocket'
            websocket = WebSocket(scope, receive=receive, send=send)
            await websocket.accept()
            Controller.is_query_params = True
            vm = await Controller.action(websocket)
            html = vm.render()
            await websocket.send_text(html)
            await websocket.close()

        Controller.is_query_params = True
        client = TestClient(app)
        
        # Test update_view => html

        with client.websocket_connect(
            Controller.build_url(
                action = 'update_view', 
                uri_name = elon_vmodel.uri_name,
                uri_id = elon_vmodel.uri_id,
                params = '{ "job" : "engineer" }'
            )) as websocket:
            response = websocket.receive_text()
            #self.assertEqual(response.status_code, 200)
            self.assertEqual(response, "Model="+str(elon.id)+" & View URI="+elon_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")
            print(response)

       

