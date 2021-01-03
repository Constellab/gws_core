import sys
import os
import unittest

from peewee import CharField

from gws.model import Model, Resource, DbManager
from gws.controller import Controller

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
        self.kv_store['age'] = age

    def get_age(self):
        return self.kv_store['age']

class FTSPerson(Model):
    _fts_model = "PersonFTSDocument"
    _fts_fields = { **Model._fts_fields, 'name': 1.0, 'city': 2.0 }
    _table_name = "ftsmodel"

class TestModel(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        PersonKVStore.drop_table()
        Person.drop_table()
        FTSPerson.drop_table()
        
        PersonKVStore.create_table()
        Person.create_table()
        FTSPerson.create_table()
        pass

    @classmethod
    def tearDownClass(cls):
        PersonKVStore.drop_table()
        Person.drop_table()
        FTSPerson.drop_table()
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

    def test_fts_model(self):
        p = FTSPerson()
        p.city = 'Petrovitchi'
        p.data['name'] = "Isaac Asimov, the author of Foundation at Trantor"
        p.save()

        p = FTSPerson()
        p.city = 'Brussels'
        p.data['name'] = "Tintin and Milou at New York"
        p.save()

        p = FTSPerson()
        p.city = 'Tokyo'
        p.data['name'] = "New York City and Tokyo"
        p.save()

        p = FTSPerson()
        p.city = 'Trantor'
        p.data['name'] = "Mister Robot"
        p.save()

        Q = FTSPerson.search("New York")
        self.assertEqual(len(Q), 2)
        for q in Q:
            print(q.get_related().data['name'])
            print(q.search_score)

        Q = FTSPerson.search("Trantor")
        for q in Q:
            print(q.get_related().data['name'])
            print(q.search_score)

    def test_model_with_kv_store(self):
        p = PersonKVStore()
        p.name = 'Isaac Asimov'
        p.set_age(30)
        p.save()

        p2 = PersonKVStore.get(PersonKVStore.name == 'Isaac Asimov')
        self.assertEqual(p2.name, 'Isaac Asimov')
        self.assertEqual(p2.get_age(), 30)

        

