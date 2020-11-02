import sys
import os
import unittest

from gws.model import Model, Resource, DbManager
from gws.controller import Controller

from peewee import CharField


############################################################################################
#
#                                        TestModel
#                                         
############################################################################################

class Person(Model):
    name = CharField(null=True)

class PersonKVStore(Model):
    name = CharField(null=True)
    def set_age(self, age):
        self.store['age'] = age

    def get_age(self):
        return self.store['age']

class TestModel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        Person.create_table()

    @classmethod
    def tearDownClass(cls):
        PersonKVStore.drop_table()
        Person.drop_table()
        pass

    def test_model(self):
        Person.create(name = 'Jhon Smith', data={})
        Person.create(name = 'Robert Vincent', data={})

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

        self.assertEqual(Person.get(Person.id == john.id).data, {'firstname': 'Alan', 'sirname': 'Smith', 'city': 'NY'})
        self.assertEqual(Person.get(Person.data['firstname'] == 'Alan').name, 'Jhon Smith')

        robert.set_data({'dog':'Milou','firstname':'Robert'})
        robert.save()
        self.assertEqual(Person.get(Person.data['firstname'] == 'Robert').name, 'Robert Vincent')
        self.assertEqual(Person.get(Person.data['dog'] == 'Milou').name, 'Robert Vincent')
        
        john.clear_data()
        john.save()
        self.assertEqual(john.data, {})
        self.assertTrue(john.store.is_connected())

    def test_model_with_kn_store(self):
        p = PersonKVStore()
        p.name = 'Isaac Asimov'
        p.set_age(30)
        self.assertFalse(p.store.is_connected())
        p.save()

        p2 = PersonKVStore.get(PersonKVStore.name == 'Isaac Asimov')
        self.assertEqual(p2.name, 'Isaac Asimov')
        self.assertEqual(p2.get_age(), 30)
        self.assertTrue(p.store.is_connected())
        self.assertTrue(p2.store.is_connected())

