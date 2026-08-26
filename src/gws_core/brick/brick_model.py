from time import time
from typing import cast

from gws_core.brick.brick_dto import (
    BrickDTO,
    BrickInfo,
    BrickMessageDTO,
    BrickMessageStatus,
    BrickStatus,
)
from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.model.typed_db_field import NullableJSONField, TypedCharField

from ..core.model.model import Model


class BrickModel(Model):
    name: TypedCharField = TypedCharField(unique=True)
    status: TypedCharField = TypedCharField()
    data: NullableJSONField = NullableJSONField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.is_saved() and not self.data:
            self.data = {}

    def _get_data(self) -> dict:
        """
        Returns the raw brick data.

        The ``data`` column is nullable in database but is always set for a BrickModel
        (initialized in the constructor and never cleared), the cast only tells the type
        checker so.

        :return: The raw brick data
        :rtype: `dict`
        """

        return cast(dict, self.data)

    def add_message(
        self, message: str, status: BrickMessageStatus, timestamp: float | None = None
    ) -> None:
        data = self._get_data()
        if "messages" not in data:
            data["messages"] = []

        if timestamp is None:
            timestamp = time()

        brick_message = {"message": message, "status": status, "timestamp": timestamp}
        data["messages"].append(brick_message)

        # update the brick status
        if status == "CRITICAL":
            self.status = "CRITICAL"
        elif status == "ERROR" and self.status != "CRITICAL":
            self.status = "ERROR"
        elif status == "WARNING" and self.status == "SUCCESS":
            self.status = "WARNING"

    def get_messages(self) -> list[BrickMessageDTO]:
        return BrickMessageDTO.from_json_list(self._get_data()["messages"])

    def clear_messages(self) -> None:
        self._get_data()["messages"] = []

    def get_brick_info(self) -> BrickInfo:
        return BrickHelper.get_brick_info_and_check(self.name)

    def get_version(self) -> str:
        return self.get_brick_info().version

    def to_dto(self) -> BrickDTO:
        brick_dto = BrickDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            name=self.name,
            status=cast(BrickStatus, self.status),
            messages=self.get_messages(),
        )

        try:
            brick_info = self.get_brick_info()
            brick_dto.version = brick_info.version
            brick_dto.repo_type = brick_info.repo_type
            brick_dto.brick_path = brick_info.path
            brick_dto.repo_commit = brick_info.repo_commit
            brick_dto.parent_name = brick_info.parent_name

        except Exception as err:
            brick_dto.messages.append(
                BrickMessageDTO(
                    message=f"Can't find brick '{self.name}', was it removed from the lab ? Error : {str(err)}",
                    status="CRITICAL",
                    timestamp=time(),
                )
            )
            brick_dto.status = "CRITICAL"

        return brick_dto

    ################################################## CLASS METHODS ##################################################

    @classmethod
    def find_by_name(cls, name: str) -> "BrickModel":
        try:
            return cls.get(cls.name == name)
        except Exception:
            return None

    @classmethod
    def clear_all_message(cls) -> None:
        BrickModel.update(data={"messages": []}).execute(cls.get_db())

    class Meta:
        table_name = "gws_brick"
        is_table = True
