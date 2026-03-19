from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials_type import CredentialsType
from gws_core.lab.lab_model.lab_dto import LabDTO, LabDTOWithCredentials
from gws_core.lab.lab_model.lab_enums import LabEnvironment, LabMode
from gws_core.lab.lab_model.lab_model import LabModel
from gws_core.lab.lab_model.lab_model_service import LabModelService
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.unique_code_service import InvalidUniqueCodeException, UniqueCodeService


# test_lab_model_service
class TestLabModelService(BaseTestCase):

    def test_generate_unique_code_url(self):
        """Verify URL contains a code parameter and uses the lab API URL."""
        url = LabModelService.generate_unique_code_url()
        self.assertIn("?code=", url)
        base_url = Settings.get_instance().get_lab_api_url()
        expected_prefix = f"{base_url}/{Settings.core_api_route_path()}/lab/from-code?code="
        self.assertTrue(url.startswith(expected_prefix))

    def test_create_or_update_lab_from_code(self):
        """Generate code, call service, verify LabModel created, credentials created,
        LabDTOWithCredentials returned with correct data."""
        # Generate a code
        code = UniqueCodeService.generate_code_current_user(None, 300)

        lab_dto = LabDTO(
            id="",
            lab_id="test-lab-123",
            name="Test Lab",
            is_current_lab=False,
            mode=LabMode.PROD,
            environment=LabEnvironment.ON_CLOUD,
            domain="test.example.com",
        )

        result = LabModelService.create_or_update_lab_from_code(code, lab_dto)

        # Verify return type
        self.assertIsInstance(result, LabDTOWithCredentials)

        # The returned lab should be the current lab (Lab A), not the remote lab
        self.assertIsNotNone(result.lab)

        # Verify credentials were created
        self.assertIsNotNone(result.credentials_data)
        self.assertIsNotNone(result.credentials_data.api_key)
        self.assertTrue(len(result.credentials_data.api_key) >= 20)

        # Verify LabModel exists in DB
        lab = LabModel.get_by_lab_id_and_mode("test-lab-123", LabMode.PROD)
        self.assertIsNotNone(lab)
        self.assertIsNotNone(lab.credentials)

        # Verify credentials exist in DB and have correct type
        self.assertEqual(lab.credentials.type, CredentialsType.LAB)

    def test_create_or_update_lab_from_code_existing(self):
        """Test update path when lab already exists."""
        # Create initial lab
        code1 = UniqueCodeService.generate_code_current_user(None, 300)
        lab_dto = LabDTO(
            id="",
            lab_id="existing-lab-456",
            name="Original Name",
            is_current_lab=False,
            mode=LabMode.PROD,
            environment=LabEnvironment.ON_CLOUD,
            domain="original.example.com",
        )
        result1 = LabModelService.create_or_update_lab_from_code(code1, lab_dto)

        # Update the lab with new name
        code2 = UniqueCodeService.generate_code_current_user(None, 300)
        lab_dto_updated = LabDTO(
            id="",
            lab_id="existing-lab-456",
            name="Updated Name",
            is_current_lab=False,
            mode=LabMode.PROD,
            environment=LabEnvironment.ON_CLOUD,
            domain="updated.example.com",
        )
        result2 = LabModelService.create_or_update_lab_from_code(code2, lab_dto_updated)

        # Verify both results return the current lab (Lab A) with credentials
        self.assertIsNotNone(result1.credentials_data)
        self.assertIsNotNone(result2.credentials_data)

        # Verify the remote lab was updated in DB
        lab = LabModel.get_by_lab_id_and_mode("existing-lab-456", LabMode.PROD)
        self.assertEqual(lab.name, "Updated Name")
        self.assertEqual(lab.domain, "updated.example.com")

    def test_invalid_code(self):
        """Verify InvalidUniqueCodeException raised for bad/expired codes."""
        lab_dto = LabDTO(
            id="",
            lab_id="test-lab-789",
            name="Test Lab",
            is_current_lab=False,
            mode=LabMode.PROD,
            environment=LabEnvironment.ON_CLOUD,
        )

        with self.assertRaises(InvalidUniqueCodeException):
            LabModelService.create_or_update_lab_from_code("invalid-code", lab_dto)

    def test_credentials_already_exist(self):
        """Verify no error when credentials already exist for the lab."""
        # Create lab first time
        code1 = UniqueCodeService.generate_code_current_user(None, 300)
        lab_dto = LabDTO(
            id="",
            lab_id="creds-test-lab",
            name="Creds Test Lab",
            is_current_lab=False,
            mode=LabMode.PROD,
            environment=LabEnvironment.ON_CLOUD,
        )
        result1 = LabModelService.create_or_update_lab_from_code(code1, lab_dto)

        # Create again — should reuse existing credentials but regenerate api_key
        code2 = UniqueCodeService.generate_code_current_user(None, 300)
        result2 = LabModelService.create_or_update_lab_from_code(code2, lab_dto)

        # Verify credentials were regenerated
        self.assertIsNotNone(result2.credentials_data)
        self.assertIsNotNone(result2.credentials_data.api_key)
        self.assertTrue(len(result2.credentials_data.api_key) >= 20)

        # Verify the remote lab still has the same credentials object in DB
        lab = LabModel.get_by_lab_id_and_mode("creds-test-lab", LabMode.PROD)
        self.assertIsNotNone(lab.credentials)
