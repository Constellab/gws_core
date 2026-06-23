from typing import final

from gws_core.core.model.model import Model
from gws_core.core.model.typed_db_field import TypedForeignKeyField, TypedJSONField
from gws_core.form.form import Form
from gws_core.form.form_dto import FormChangeEntry, FormSaveEventDTO
from gws_core.user.user import User


@final
class FormSaveEvent(Model):
    """Audit row written once per Form save. The full per-leaf change list lives
    in the `changes` JSON column. See form_feature.md §3.4."""

    form = TypedForeignKeyField(Form, on_delete="CASCADE", null=False, backref="save_events")
    user = TypedForeignKeyField(User, null=False, backref="+")

    # List of FormChangeEntry dicts.
    changes = TypedJSONField(null=False)

    def get_changes(self) -> list[FormChangeEntry]:
        raw = self.changes or []
        return [FormChangeEntry.from_json(entry) for entry in raw]

    def set_changes(self, entries: list[FormChangeEntry]) -> None:
        self.changes = [entry.to_json_dict() for entry in entries]

    def to_dto(self) -> FormSaveEventDTO:
        return FormSaveEventDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            form_id=self.form_id,
            user=self.user.to_dto(),
            changes=self.get_changes(),
        )

    class Meta:
        table_name = "gws_form_save_event"
        is_table = True
        indexes = (
            (("form", "created_at"), False),
            (("user", "created_at"), False),
        )
