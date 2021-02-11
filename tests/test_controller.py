
import unittest
import copy
import json

from gws.model import Model, Resource, Viewable
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
    _is_deletable = True
    
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

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

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        pass

    def test_get_model(self):
        elon = Person()
        elon.set_name('Elon Musk')
        elon.save()

        response = Controller.action(action="get", object_type=elon.full_classname(), object_uri=elon.uri, return_format="json")
        print(response)
        self.assertEqual(response["model"]["uri"], elon.uri)

    def test_update_view_model(self):
        elon = Person()
        elon.set_name('Elon Musk')
        elon.save()

        view_model = elon.view()
        view_model.save()
        data = {"job" : "Tesla Maker"}

        response = Controller.action(action="update", object_type=view_model.full_classname(), object_uri=view_model.uri, data=data, return_format="json")
        self.assertEqual(response["uri"], view_model.uri)
        self.assertEqual(response["data"]["params"], {'job': 'Tesla Maker'})

    def test_delete_view_model(self):
        elon = Person()
        elon.set_name('Elon Musk')
        elon.save()

        view_model = elon.view()
        view_model.save()
        self.assertFalse(view_model.is_deleted)
        
        self.assertRaises(Exception, Controller.action, action="delete", object_type=elon.full_classname(), object_uri=elon.uri, return_format="json")
        
        view_model = Controller.action(action="delete", object_type=view_model.full_classname(), object_uri=view_model.uri)
        self.assertTrue(view_model.is_deleted)
        
        
    def test_register_model(self):
        Controller.register_all_processes()
        
        from gws.model import Process
        
        count = Process.select().count()
        print(f"Process counts = {count}")
        for Q in Process.select():
            print(Q.type)
