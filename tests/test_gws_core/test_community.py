from gws_core.community.community_service import CommunityService
from gws_core.test.base_test_case import BaseTestCase
from gws_core.user.auth_service import AuthService
from gws_core.user.user import User
from gws_core.user.user_dto import UserFullDTO, UserTheme
from gws_core.user.user_group import UserGroup
from gws_core.user.user_service import UserService


class TestCommunity(BaseTestCase):
    """
    def test_get_community_available_live_tasks(self):

        user_dto = UserFullDTO(
            id="b736c9b0-b7a9-463f-a3ed-bb6419d43373",
            email="test_mail@gencovery.com",
            first_name="Firstname test",
            last_name="Lastname test",
            group=UserGroup.USER,
            is_active=True,
            theme=UserTheme.LIGHT_THEME,
        )
        UserService.create_or_update_user_dto(user_dto)

        token = AuthService.generate_user_access_token(user_dto.id)

        user_data: User = AuthService.check_user_access_token(token)

        res = CommunityService().get_community_available_live_tasks([], '', False, 0, 10)
        self.assertNotEqual(len(res['objects']), 0)

    def test_create_community_live_task_version(self):

        community_live_task_version = CommunityService().create_community_live_task_version({}, 'b736c9b0-b7a9-463f-a3ed-bb6419d43373')

    """