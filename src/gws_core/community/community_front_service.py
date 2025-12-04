from typing import Literal

from gws_core.core.utils.settings import Settings
from gws_core.model.typing_name import TypingNameObj


class CommunityFrontService:
    @classmethod
    def get_typing_doc_url(
        cls, typing_name: str, brick_major_version: int | Literal["latest"] = "latest"
    ) -> str:
        typing_name_obj = TypingNameObj.from_typing_name(typing_name)
        brick_version_str = (
            "latest" if brick_major_version == "latest" else "v" + str(brick_major_version)
        )

        object_type: str = None
        if typing_name_obj.object_type == "TASK":
            object_type = "task"
        elif typing_name_obj.object_type == "RESOURCE":
            object_type = "resource"
        else:
            raise Exception(
                f"Object with type '{typing_name_obj.object_type}' are not documented in community"
            )

        return f"{cls.get_url()}/bricks/{typing_name_obj.brick_name}/{brick_version_str}/doc/technical-folder/{object_type}/{typing_name_obj.unique_name}"

    @classmethod
    def get_url(cls):
        return Settings.get_community_front_url()
