
import unittest

from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.prism.app import App
from gws.prism.model import Model, Resource, ResourceViewModel
from gws.prism.view import HTMLViewTemplate, JSONViewTemplate, ViewTemplateFile
from gws.prism.controller import Controller

import os
__cdir__ = os.path.dirname(os.path.abspath(__file__))

from gws.settings import Settings
settings = Settings.retrieve()
print(settings.db_path)

class Person(Resource):
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

class PersonHTMLViewModel(ResourceViewModel):
    template = HTMLViewTemplate("I am <b>{{view_model.model.name}}</b>! My job is {{view_model.data.job}}.")

class PersonJSONViewModel(ResourceViewModel):
    template = JSONViewTemplate('{"name": "{{view_model.model.name}}!", "job":"{{view_model.data.job}}"}')

class FunnyView(ResourceViewModel):
    template = ViewTemplateFile(os.path.join(__cdir__, 'test-view/funny-view.html'), type="html")

Controller.register_model_classes([Person, PersonHTMLViewModel, PersonJSONViewModel])

class TestHTMLView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Controller.reset()
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        Person.drop_table()
        pass
    
    def test_view(self):
        elon = Person()
        view_model = PersonHTMLViewModel(elon)
        self.assertEqual(view_model.data, {})

        elon.set_name('Elon Musk')
        params = {"job" : "engineer"}
        html = view_model.render(params)
        print(html)

        self.assertEqual(html, "I am <b>Elon Musk</b>! My job is engineer.")
        self.assertEqual(view_model.data, params)
        self.assertEqual(view_model.data, params)

        self.assertTrue( view_model.model is elon )
        self.assertTrue( view_model.id is None )
        self.assertTrue( elon.id is None )
        
        Controller.register_model_instances([elon, view_model])
        self.assertEqual(len(Controller.models), 2)
        Controller.save_all()

        self.assertEqual(len(Controller.models), 2)

        vm = PersonHTMLViewModel.get_by_id(view_model.id)
        self.assertEqual(vm, view_model)
        self.assertEqual(vm.model, elon)

        self.assertEqual(len(Controller.models), 2)

class TestJSONView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Controller.reset()
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass
    
    def test_view(self):
        elon = Person()
        view_model = PersonJSONViewModel(elon)
        elon.set_name('Elon Musk')

        params = {"job" : "engineer"}
        json_text = view_model.render(params)
        print(json_text)

        self.assertEqual(json_text, '{"name": "Elon Musk!", "job":"engineer"}')
        self.assertEqual(view_model.data, params)
        self.assertEqual(view_model.data, params)
        self.assertEqual(view_model.model.id, None)
        self.assertEqual(view_model.id, None)

        self.assertEqual(len(Controller.models), 0)
        
        view_model.save()     #save the model and view_model
        
        self.assertTrue(isinstance(view_model.model.id, int))
        self.assertTrue(isinstance(view_model.id, int))

        # retrieve the view_model
        vmodel2 = PersonJSONViewModel.get( PersonJSONViewModel.id == view_model.id )
        self.assertEqual(vmodel2.id, view_model.id)
        self.assertEqual(vmodel2.model.id, view_model.model.id)

        self.assertEqual(len(Controller.models), 0)

class TestFunnyView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Controller.reset()
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        PersonHTMLViewModel.drop_table()
        PersonJSONViewModel.drop_table()
        pass

    
    def test_view_file(self):
        elon = Person()
        view_model = FunnyView(elon)
        elon.set_name('Elon')

        text = view_model.render({})
        print(text)

        expected_text = """
        <div>
            This is my funny view!<br>
            My name is: Elon
        </div>
        """
        self.assertEqual(expected_text.replace("\n", "").replace(" ", ""), text.replace("\n", "").replace(" ", ""))

    def test_default_view_file(self):
        elon = Person()
        view_model = ResourceViewModel(elon)
        elon.set_name('Elon Musk')
        
        view_model.save()

        text = view_model.render({})
        print(text)

        expected_text = "<x-gws class='gws-model' id='{}' data-id='{}' data-uri='{}'></x-gws>".format(view_model._uuid, view_model.id, view_model.uri)

        self.assertEqual(expected_text.replace("\n", "").replace(" ", ""), text.replace("\n", "").replace(" ", ""))