
import unittest
import copy
import json
import asyncio

from gws.model import Model, Resource, Viewable, ViewModel
from gws.controller import Controller
from gws.http import *

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
        ViewModel.drop_table()
        Home.drop_table()
        Person.drop_table()

    @classmethod
    def tearDownClass(cls):
        ViewModel.drop_table()
        Person.drop_table()
        pass

    def test_get_model(self):
        
        async def action():
            elon = Person()
            elon.set_name('Elon Musk')
            elon.save()

            response = await Controller.action(
                action="get", 
                object_type=elon.full_classname(), 
                object_uri=elon.uri
            )
            
            self.assertEqual(response["model"]["uri"], elon.uri)
        
        asyncio.run( action() )
        
    def test_update_view_model(self):
        
        async def action():
            elon = Person()
            elon.set_name('Elon Musk')
            elon.save()

            view_model = elon.view()
            view_model.save()
            data = {"job" : "Tesla Maker"}

            response = await Controller.action(
                action="update", 
                object_type=view_model.full_classname(), 
                object_uri=view_model.uri, 
                data=data
            )
            
            self.assertEqual(response["uri"], view_model.uri)
            self.assertEqual(response["data"]["params"], {'job': 'Tesla Maker'})
        
        asyncio.run( action() )
        
    def test_archive_view_model(self):
        
        async def action():
            elon = Person()
            elon.set_name('Elon Musk')
            elon.save()

            view_model = elon.view()
            view_model.save()
            self.assertFalse(view_model.is_archived)
        
            with self.assertRaises(HTTPNotFound):
                response = await Controller.action(
                    action="archive", 
                    object_type=elon.full_classname(), 
                    object_uri=elon.uri
                )
            
            response = await Controller.action(
                action="archive", 
                object_type=view_model.full_classname(), 
                object_uri=view_model.uri
            )
            self.assertEqual(response["uri"], view_model.uri)
            self.assertEqual(response["is_archived"], True)
            
        asyncio.run( action() )
        
    def test_register_model(self):
        Controller.register_all_processes()
        
        from gws.model import Process
        
        count = Process.select().count()
        print(f"Process counts = {count}")
        for Q in Process.select():
            print(Q.type)
        
        # check that the number of process has not change
        Controller.register_all_processes()
        self.assertEqual(count, Process.select().count())