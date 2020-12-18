
import unittest
import copy
import json

from gws.model import Model, Resource, HTMLViewModel, JSONViewModel, Viewable
from gws.view import HTMLViewTemplate, JSONViewTemplate
from gws.controller import Controller

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

class TestControllerHTTP(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Home.drop_table()
        Person.drop_table()
        Viewable.drop_table()

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()    
        pass

    def test_get_model(self):
        elon = Person()
        html_vmodel = HTMLPersonViewModel(model=elon)
        json_vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        self.assertEqual(Controller.fetch_model(html_vmodel.full_classname(), html_vmodel.uri), html_vmodel )

        # assert that local import does not affect class
        data = { "job" : "engineer"}
        html_vmodel.set_data(data)
        html_vmodel.save()
        self.assertEqual(Controller.fetch_model(html_vmodel.full_classname(), html_vmodel.uri), html_vmodel)

        response = Controller.action(action="get", object_type=html_vmodel.full_classname(), object_uri=html_vmodel.uri, return_format="json")
        self.assertEqual(response["uri"], html_vmodel.uri)

    def test_put_model(self):
        elon = Person()
        html_vmodel = HTMLPersonViewModel(model=elon)
        json_vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        data = {"job" : "engineer"}
        json_vmodel.set_data(data)
        json_vmodel.save()
        self.assertEqual(Controller.fetch_model(html_vmodel.full_classname(), html_vmodel.uri), html_vmodel)

        data = {"vdata" : { "job" : "Tesla Maker" } }
        response = Controller.action(action="put", object_type=json_vmodel.full_classname(), object_uri=json_vmodel.uri, data=data, return_format="json")
        self.assertEqual(response["uri"], json_vmodel.uri)
        self.assertEqual(response["data"], {'job': 'Tesla Maker'})

    def test_post_model(self):
        elon = Person()
        html_vmodel = HTMLPersonViewModel(model=elon)
        json_vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        # Create JSONView from HTMLView
        data = { 
            "vdata" : { "job" : "SpaceX CEO" }, 
            "type" : "tests.test_controller.JSONPersonViewModel"
        }
        response = Controller.action(action="post", object_type=html_vmodel.full_classname(), object_uri=html_vmodel.uri, data=data, return_format="json")
        self.assertNotEqual(response["uri"], html_vmodel.uri)
        self.assertEqual(response["data"], { "job" : "SpaceX CEO" })

        # Check that the vmodels are registered to their conrresponding models
        k = HTMLPersonViewModel.full_classname()
        self.assertEquals(Person._vmodel_specs[k], HTMLPersonViewModel)

    def test_post_model_raise_error(self):
        bill = Person()
        bill.set_name('Bill Gate')
        bill.save()

        data = { "mdata": {"name": "Bill Gate From Microsoft"} }
        self.assertRaises(Exception, Controller.action, action="post", object_type=bill.full_classname(), object_uri=bill.uri, data=data, return_format="json")

    def test_delete_model(self):
        elon = Person()
        html_vmodel = HTMLPersonViewModel(model=elon)
        json_vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        self.assertRaises(Exception, Controller.action, action="delete", object_type=type(elon), object_uri=elon.uri, return_format="json")
        Controller.action(action="delete", object_type=html_vmodel.full_classname(), object_uri=html_vmodel.uri)
        delete_vm = HTMLPersonViewModel.get_by_id(html_vmodel.id)
        self.assertTrue(delete_vm.is_deleted)
        
        
    def test_register_model(self):
        Controller.register_all_processes()
        
        from gws.model import Process
        
        count = Process.select().count()
        print(f"Process counts = {count}")
        for Q in Process.select():
            print(Q.type)
