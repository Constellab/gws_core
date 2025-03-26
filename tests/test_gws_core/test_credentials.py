

from gws_core.config.config_specs import ConfigSpecs
from gws_core.core.classes.search_builder import (SearchFilterCriteria,
                                                  SearchOperator, SearchParams)
from gws_core.credentials.credentials import Credentials
from gws_core.credentials.credentials_param import CredentialsParam
from gws_core.credentials.credentials_service import CredentialsService
from gws_core.credentials.credentials_type import (CredentialsDataOther,
                                                   CredentialsType,
                                                   SaveCredentialsDTO)
from gws_core.test.base_test_case import BaseTestCase


# test_credentials
class TestCredentials(BaseTestCase):

    def test_crud(self):
        save_dto: SaveCredentialsDTO = SaveCredentialsDTO(
            name="test",
            type=CredentialsType.OTHER,
            description="test",
            data={"data": [{"key": "test", "value": "test"}]}
        )

        first_credentials = CredentialsService.create(save_dto)
        self.assertIsNotNone(first_credentials.id)
        self.assertEqual(first_credentials.name, save_dto.name)
        self.assertEqual(first_credentials.type, save_dto.type)
        self.assertEqual(first_credentials.description, save_dto.description)
        self.assert_json(first_credentials.data, save_dto.data)

        save_dto.name = "test2"
        first_credentials = CredentialsService.update(first_credentials.id, save_dto)
        self.assertEqual(first_credentials.name, save_dto.name)

        save_dto2: SaveCredentialsDTO = SaveCredentialsDTO(
            name="hello",
            type=CredentialsType.S3,
            data={"endpoint_url": "test", "region": "test", "access_key_id": "test", "secret_access_key": "test"}
        )
        CredentialsService.create(save_dto2)

        # test search by name
        search_dict: SearchParams = SearchParams(
            filtersCriteria=[SearchFilterCriteria(key="name", operator=SearchOperator.CONTAINS, value="est")])
        search_result = CredentialsService.search(search_dict)
        self.assertEqual(search_result.page_info.total_number_of_items, 1)
        self.assertEqual(search_result.results[0].name, "test2")

        # Test search by name and type
        search_dict.add_filter_criteria(key="type", operator=SearchOperator.EQ, value=CredentialsType.OTHER)
        search_result = CredentialsService.search(search_dict)
        self.assertEqual(search_result.page_info.total_number_of_items, 1)
        self.assertEqual(search_result.results[0].name, "test2")

        # Test json
        json_ = first_credentials.to_dto()
        self.assertEqual(json_.name, first_credentials.name)

        # Test delete
        CredentialsService.delete(first_credentials.id)
        self.assertIsNone(Credentials.get_by_id(first_credentials.id))

    def test_credentials_params(self):
        credentials = Credentials()
        credentials.name = "9999"
        credentials.type = CredentialsType.OTHER
        credentials.data = {"data": [{"key": "test", "value": "test"}]}
        credentials.save()

        config_params = ConfigSpecs(
            {"credentials": CredentialsParam(credentials_type=CredentialsType.OTHER)}).build_config_params(
            {"credentials": credentials.name})

        data: CredentialsDataOther = config_params["credentials"]
        self.assertIsInstance(data, CredentialsDataOther)
        self.assertEqual(data.data["test"], "test")
        self.assertIsNotNone(data.meta)
