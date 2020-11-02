
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
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        Viewable.drop_table()
        
        # Person.create_table()
        # HTMLPersonViewModel.create_table()
        # JSONPersonViewModel.create_table()

    @classmethod
    def tearDownClass(cls):
        # Person.drop_table()
        # HTMLPersonViewModel.drop_table()
        # JSONPersonViewModel.drop_table()    
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
        self.assertEqual(html_vmodel.render(), "Model="+str(elon.id)+" & View URI="+html_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")

        vm = Controller.action(action="get", rtype=html_vmodel.full_classname(), uri=html_vmodel.uri)
        self.assertEqual(vm, html_vmodel)
        self.assertEqual(vm.render(), "Model="+str(elon.id)+" & View URI="+html_vmodel.uri+": I am <b>Elon Musk</b>! My job is engineer.")

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
        self.assertEqual(json_vmodel.render(), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"engineer"}')

        data = {"vdata" : { "job" : "Tesla Maker" } }
        vm = Controller.action(action="put", rtype=json_vmodel.full_classname(), uri=json_vmodel.uri, data=data)
        self.assertEqual(vm.render(), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"Tesla Maker"}')

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
        new_json_view = Controller.action(action="post", rtype=html_vmodel.full_classname(), uri=html_vmodel.uri, data=data)
        self.assertNotEqual(new_json_view.render(), '{"model_id":"'+str(elon.id)+'", "view_uri":"'+json_vmodel.uri+'", "name": "Elon Musk!", "job":"SpaceX CEO"}')

        self.assertEqual(type(new_json_view), JSONPersonViewModel)
        self.assertFalse(new_json_view is json_vmodel)
        self.assertEqual(new_json_view.model, elon)

        # Check that the vmodels are registered to their conrresponding models
        k = HTMLPersonViewModel.full_classname()
        self.assertEquals(Person._vmodel_specs[k], HTMLPersonViewModel)

    #def test_post_system_trackable_model_raise_error(self):
    def test_post_model_raise_error(self):
        bill = Person()
        bill.set_name('Bill Gate')
        bill.save()

        data = { "mdata": {"name": "Bill Gate From Microsoft"} }
        self.assertRaises(Exception, Controller.action, action="post", rtype=bill.full_classname(), uri=bill.uri, data=data)

    def test_delete_model(self):
        elon = Person()
        html_vmodel = HTMLPersonViewModel(model=elon)
        json_vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')
        
        elon.save()
        html_vmodel.save()
        json_vmodel.save()

        self.assertRaises(Exception, Controller.action, action="delete", rtype=type(elon), uri=elon.uri)
        vmodel = Controller.action(action="delete", rtype=html_vmodel.full_classname(), uri=html_vmodel.uri)
        self.assertTrue(vmodel.is_deleted)