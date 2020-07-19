import sys
import os
import unittest

from gws.prism.model import Model, Resource, DbManager
from gws.prism.controller import Controller

from peewee import CharField


############################################################################################
#
#                                        TestModel
#                                         
############################################################################################

class Person(Model):
    name = CharField(null=True)

Controller.register_model_classes([Person])

class TestModel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        Person.create_table()
        Person.create(name = 'Jhon Smith', data={})
        Person.create(name = 'Robert Vincent', data={})

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        pass

    def test_db_object(self):
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

        john.insert_data({'firstname':'Alan'})
        john.save()
        self.assertEqual(john.data['firstname'], 'Alan')

        # print(Person.get(Person.id == john.id).data)
        # print(john.id)

        self.assertEqual(Person.get(Person.id == john.id).data, {'firstname': 'Alan', 'sirname': 'Smith', 'city': 'NY'})
        self.assertEqual(Person.get(Person.data['firstname'] == 'Alan').name, 'Jhon Smith')

        robert.set_data({'dog':'Milou','firstname':'Robert'})
        robert.save()
        self.assertEqual(Person.get(Person.data['firstname'] == 'Robert').name, 'Robert Vincent')
        self.assertEqual(Person.get(Person.data['dog'] == 'Milou').name, 'Robert Vincent')
        
        john.clear_data()
        john.save()
        self.assertEqual(john.data, None)

