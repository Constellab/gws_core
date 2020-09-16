
import unittest
import copy
import json

from peewee import CharField, ForeignKeyField
from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient
from starlette.websockets import WebSocket

from gws.app import App
from gws.model import Model, Resource, HTMLViewModel, JSONViewModel, Viewable
from gws.view import HTMLViewTemplate, JSONViewTemplate
from gws.controller import Controller
from gws.base import slugify

# ##############################################################################
#
# Class definition
#
# ##############################################################################


class Home(Viewable):
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

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

# ##############################################################################
#
# Testing
#
# ##############################################################################

# we suppose that the request comes from the view
# url = "/action/{uri}/{data}",
async def app(scope, receive, send):
    assert scope['type'] == 'http'
    request = Request(scope, receive)
    vm = await Controller.action(request)
    html = vm.render()
    response = HTMLResponse(html)
    await response(scope, receive, send)


class TestControllerHTTP(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Home.drop_table()
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()

        Person.create_table()
        HTMLPersonViewModel.create_table()
        JSONPersonViewModel.create_table()

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()    

    def test_read_model(self):
        print("")
        print("# Controller testing: read model")
        print("# -----------------")

        elon = Person()
        html_vmodel = HTMLPersonViewModel(elon)
        json_vmodel = JSONPersonViewModel(elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        self.assertEqual( Controller.fetch_model(html_vmodel.uri), html_vmodel )

        # assert that local import does not affect class
        from gws.controller import Controller as Ctrl
        self.assertEqual(Ctrl.fetch_model(html_vmodel.uri), html_vmodel)

        #self.assertEqual(Ctrl.models, Controller.models)
        
        Controller.is_query_params = True
        client = TestClient(app)

        # Test update_view => html
        data = '{"vdata" : { "job" : "engineer"} }'
        response = client.get(Controller.build_url(
            action = "read", 
            uri = html_vmodel.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), "Model="+str(elon.id)+" & View URI="+html_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")
        print(response.content)

        # Test update_view => json
        data = '{"vdata" : { "job" : "engineer" } }'
        response = client.get(Controller.build_url(
            action = "read", 
            uri = json_vmodel.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"engineer"}')
        print(response.content)

        # Test update_view different data => json
        data = '{"vdata" : { "job" : "Tesla Maker" } }'
        response = client.get(Controller.build_url(
            action = "read", 
            uri = json_vmodel.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"Tesla Maker"}')
        print(response.content)
        
        # Read JSONView
        data = '{ "vdata" : { "job" : "SpaceX CEO" } }'
        response = client.get(Controller.build_url(
            action = "read", 
            uri = json_vmodel.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"SpaceX CEO"}')
  
        # Create JSONView form HTMLView
        data = """
            {
                "vdata" : { "job" : "SpaceX CEO" }, 
                "target" : "tests-test-controller-jsonpersonviewmodel"
            }
        """
        response = client.get(Controller.build_url(
            action = "create", 
            uri = html_vmodel.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.decode("utf-8"), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"SpaceX CEO"}')
        json_response = json.loads(response.content.decode("utf-8"))
        new_uri = json_response["view_uri"]
        new_json_view = Controller.fetch_model(new_uri)

        self.assertEqual(type(new_json_view), JSONPersonViewModel)
        self.assertFalse(new_json_view is json_vmodel)
        self.assertEqual(new_json_view.model, elon)
        print(response.content)

        # Check that the vmodels a registered to their conrresponding models
        k = slugify(HTMLPersonViewModel.full_classname())
        self.assertEquals(Person._vmodel_specs[k], HTMLPersonViewModel)

    def test_create_system_trackable_model_error(self):
        print("")
        print("# Controller testing: create system trackable model")
        print("# -----------------")

        bill = Person()
        bill.set_name('Bill Gate')
        bill.save()

        Controller.is_query_params = True
        client = TestClient(app)
        
        data = '{ "mdata": {"name": "Bill Gate From Microsoft"} }'
        try:
            client.get(Controller.build_url(
                action = "create", 
                uri = bill.uri,
                data = data
            ))
            is_system_trackable_altered = True
        except:
            is_system_trackable_altered = False
        finally:
            self.assertFalse(is_system_trackable_altered)
    

    def test_create_model(self):
        print("")
        print("# Controller testing: create model")
        print("# -----------------")

        home = Home()
        home.set_name('Good Home!')
        home.save()

        Controller.is_query_params = True
        client = TestClient(app)
        
        data = '{ "mdata": {"name": "Good Blue Home!"} }'
        response = client.get(Controller.build_url(
            action = "create", 
            uri = home.uri,
            data = data
        ))
        self.assertEqual(response.status_code, 200)

        Q = Home.select_me()

        self.assertEqual(len(Q), 2)
        self.assertEqual(Q[0].data, {'name': 'Good Home!'})
        self.assertEqual(Q[1].data, {'name': 'Good Blue Home!'})

        data = '{ "mdata": {"name": "Good Blue and Red Home!"} }'
        response = client.get(Controller.build_url(
            action = "update", 
            uri = home.uri,
            data = data
        ))

        h = Home.select().where(Home.data['name'] == 'Good Blue & Red Home!')
        self.assertEqual(h, home)

# class TestControllerWebSocket(unittest.TestCase):
    
#     @classmethod
#     def setUpClass(cls):
#         Person.create_table()
#         HTMLPersonViewModel.create_table()
#         JSONPersonViewModel.create_table()
#         pass

#     @classmethod
#     def tearDownClass(cls):
#         Person.drop_table()
#         HTMLPersonViewModel.drop_table()
#         JSONPersonViewModel.drop_table()
#         pass
    
#     def test_controller(self):
#         print("")
#         print("# WebSocket Testing")
#         print("# -----------------")

#         elon = Person()
#         html_vmodel = HTMLPersonViewModel(elon)
#         elon.set_name('Elon Musk')
                
#         elon.save()
#         html_vmodel.save()

#         self.assertEqual(Controller.fetch_model(html_vmodel.uri), html_vmodel)

#         # we suppose that the request comes from the view
#         # url = "/action/{uri}/{data}",
#         async def app(scope, receive, send):
#             assert scope['type'] == 'websocket'
#             websocket = WebSocket(scope, receive=receive, send=send)
#             await websocket.accept()
#             Controller.is_query_params = True
#             vm = await Controller.action(websocket)
#             html = vm.render()
#             await websocket.send_text(html)
#             await websocket.close()

#         Controller.is_query_params = True
#         client = TestClient(app)
        
#         # Test update_view => html

#         with client.websocket_connect(
#             Controller.build_url(
#                 action = "read", 
#                 uri = html_vmodel.uri,
#                 data = '{"vdata" : { "job" : "engineer"} }'
#             )) as websocket:
#             response = websocket.receive_text()
#             #self.assertEqual(response.status_code, 200)
#             self.assertEqual(response, "Model="+str(elon.id)+" & View URI="+html_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")
#             print(response)

       

