
import unittest
from gws.model import User, Project, Experiment
from gws.central import Central

class TestCentral(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        Project.drop_table()
        User.drop_table()
        Experiment.drop_table()

    @classmethod
    def tearDownClass(cls):
        pass

    def test_central(self):
        data = {
            "firstname": "Alan", 
            "sirname": "Peter",
            "organization": "gencovery",
            "email": "alan@gencorery.com",
            "token": 'my_token'
        }
        tf = Central.create_user("1234567890", data)
        self.assertTrue(tf)
        user = User.get_by_uri("1234567890")
        self.assertEqual(user.email, "alan@gencorery.com")
        self.assertEqual(user.token, "my_token")


        data = {
            "name": "My awesome project", 
            "organization": "gencovery"
        }
        tf = Central.create_project("azerty123456789", data)
        self.assertTrue(tf)
        project = Project.get_by_uri("azerty123456789")
        self.assertEqual(project.name, "My awesome project")


        data = {
            "user_uri": "1234567890", 
            "project_uri": "azerty123456789"
        }
        Central.create_experiment("123456abcd", data)
        self.assertTrue(tf)
        e = Experiment.get_by_uri("123456abcd")
        self.assertEqual(e.user, user)
        self.assertEqual(e.project, project)
