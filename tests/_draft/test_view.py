

import os
import unittest

from starlette.requests import Request
from starlette.responses import JSONResponse, HTMLResponse
from starlette.testclient import TestClient

from gws.app import App
from gws.model import Model, Resource
from gws.view import HTMLViewTemplate
from gws.controller import Controller
from gws.settings import Settings

settings = Settings.retrieve()
testdata_dir = settings.get_dir("gws:testdata_dir")

class Person(Resource):
    @property
    def name(self):
        return self.data['name']
    
    def set_name(self, name):
        self.data['name'] = name

class HTMLPersonViewModel(HTMLViewModel):
    model_specs = [Person]
    template = HTMLViewTemplate("I am <b>{{vmodel.model.name}}</b>! My job is {{vmodel.data.job}}.")

class JSONPersonViewModel(JSONViewModel):
    model_specs = [Person]
    template = JSONViewTemplate('{"name": "{{vmodel.model.name}}!", "job":"{{vmodel.data.job}}"}')

class FunnyViewModel(HTMLViewModel):
    model_specs = [Person]
    template = ViewTemplateFile(os.path.join(testdata_dir, './funny-view.html'), type="html")


class TestJSONView(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass
    
    def test_view(self):
        elon = Person()
        vmodel = JSONPersonViewModel(model=elon)
        elon.set_name('Elon Musk')

        params = {"job" : "engineer"}
        json_text = vmodel.render(params)
        print(json_text)

        self.assertEqual(json_text, '{"name": "Elon Musk!", "job":"engineer"}')
        self.assertEqual(vmodel.data, params)
        self.assertEqual(vmodel.data, params)
        self.assertEqual(vmodel.model.id, None)
        self.assertEqual(vmodel.id, None)
        
        vmodel.save()     #save the model and vmodel
        
        self.assertTrue(isinstance(vmodel.model.id, int))
        self.assertTrue(isinstance(vmodel.id, int))

        # retrieve the vmodel
        vmodel2 = JSONPersonViewModel.get( JSONPersonViewModel.id == vmodel.id )
        self.assertEqual(vmodel2.id, vmodel.id)
        self.assertEqual(vmodel2.model.id, vmodel.model.id)

class TestFunnyView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass

    @classmethod
    def tearDownClass(cls):
        Person.drop_table()
        HTMLPersonViewModel.drop_table()
        JSONPersonViewModel.drop_table()
        pass

    
    def test_view_file(self):
        elon = Person()
        vmodel = FunnyViewModel(model=elon)
        elon.set_name('Elon')

        text = vmodel.render({})
        print(text)

        expected_text = """
        <div>
            This is my funny view!<br>
            My name is: Elon
        </div>
        """
        self.assertEqual(expected_text.replace("\n", "").replace(" ", ""), text.replace("\n", "").replace(" ", ""))