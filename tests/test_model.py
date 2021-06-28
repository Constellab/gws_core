# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

import sys
import os
import unittest

from peewee import CharField
from gws.model import Model, Resource
from gws.unittest import GTest
from gws.service.model_service import ModelService
from gws.unittest import GTest

############################################################################################
#
#                                        TestModel
#                                         
############################################################################################

#Model._db_manager.init(engine="mariadb")

class Person(Model):
    name = CharField(null=True)
    _table_name = 'test_person'

class TestModel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        GTest.drop_tables()
        GTest.create_tables()
        Person.create_table()

    @classmethod
    def tearDownClass(cls):
        GTest.drop_tables()
        Person.drop_table()

    def test_model(self):
        GTest.print("Test Model")
        p1 = Person(name = 'Jhon Smith', data={})
        p1.save()
        p2 = Person(name = 'Robert Vincent', data={})
        p2.save()
        john = Person.get(Person.name == 'Jhon Smith')
        robert = Person.get(Person.name == 'Robert Vincent')
        john.set_data({
            'firstname':'Jhon',
            'sirname':'Smith', 
            'city': 'NY'
        })
        john.save()
        self.assertEqual(john.name, 'Jhon Smith')
        self.assertEqual(john.data['firstname'], 'Jhon')
        self.assertEqual(john.data['sirname'], 'Smith')

        john.data['firstname'] = 'Alan'
        john.save()
        self.assertEqual(john.data['firstname'], 'Alan')

        john2 = Person.get_by_id(john.id)
        self.assertEqual(john2.data, john.data)

        john.clear_data()
        john.save()
        self.assertEqual(john.data, {})
        self.assertTrue(john.verify_hash())

    def test_model_registrering(self):
        ModelService.register_all_processes_and_resources()
        self.assertTrue( len(ModelService._model_types) != 0 )
        from gws.json import JSONLoader
        from gws.csv import CSVImporter
        self.assertTrue( JSONLoader.full_classname() in ModelService._model_types )
        self.assertTrue( CSVImporter.full_classname() in ModelService._model_types )


