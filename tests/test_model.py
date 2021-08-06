# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com


import unittest

from gws_core import CSVImporter, GTest, JSONLoader, Model, ModelService
from peewee import CharField

############################################################################################
#
#                                        TestModel
#
############################################################################################


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
        GTest.print("Model")
        p1: Person = Person(name='John Smith', data={})
        p1.save()
        p2: Person = Person(name='Robert Vincent', data={})
        p2.save()
        john: Person = Person.get(Person.name == 'John Smith')
        john.set_data({
            'firstname': 'John',
            'sirname': 'Smith',
            'city': 'NY'
        })
        john.save()
        self.assertEqual(john.name, 'John Smith')
        self.assertEqual(john.data['firstname'], 'John')
        self.assertEqual(john.data['sirname'], 'Smith')

        john.data['firstname'] = 'Alan'
        john.save()
        self.assertEqual(john.data['firstname'], 'Alan')

        john2: Person = Person.get_by_id(john.id)
        self.assertEqual(john2.data, john.data)

        john.clear_data()
        john.save()
        self.assertEqual(john.data, {})
        self.assertTrue(john.verify_hash())

        # check that john2 has not changed until refresh
        self.assertEqual(john2.data, {
            'firstname': 'Alan',
            'sirname': 'Smith',
            'city': 'NY'
        })
        john2.refresh()
        self.assertEqual(john2.data, {})

    def test_model_registrering(self):
        GTest.print("Model Registering")
        self.assertTrue(len(ModelService.get_model_types()) != 0)

        self.assertTrue(JSONLoader.full_classname()
                        in ModelService.get_model_types())
        self.assertTrue(CSVImporter.full_classname()
                        in ModelService.get_model_types())
