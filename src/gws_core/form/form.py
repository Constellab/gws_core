from typing import Any, final

from peewee import BooleanField, CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.db_field import DateTimeUTC, JSONField
from gws_core.core.model.model_with_user import ModelWithUser
from gws_core.form.form_dto import FormDTO, FormFullDTO, FormStatus
from gws_core.form_template.form_template_version import FormTemplateVersion
from gws_core.user.user import User


@final
class Form(ModelWithUser):
    """An instance of a FormTemplateVersion filled (or being filled) with values."""

    name = CharField(max_length=255, null=False)

    # FK is non-cascading: deleting a version that has Forms is forbidden at
    # the service layer (Phase 2). Forms outlive the version they were minted
    # from for as long as the version is not hard-deleted.
    template_version: FormTemplateVersion = ForeignKeyField(
        FormTemplateVersion, null=False, backref="forms"
    )

    status: FormStatus = EnumField(
        choices=FormStatus, default=FormStatus.DRAFT, index=True
    )

    submitted_at = DateTimeUTC(null=True)
    submitted_by = ForeignKeyField(User, null=True, backref="+")

    # Field values keyed by ConfigSpecs key; ParamSet items carry __item_id.
    values: dict[str, Any] = JSONField(null=True)

    is_archived = BooleanField(default=False, index=True)

    def to_dto(self) -> FormDTO:
        return FormDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            template_version_id=self.template_version_id,
            status=self.status,
            submitted_at=self.submitted_at,
            submitted_by=self.submitted_by.to_dto() if self.submitted_by else None,
            is_archived=self.is_archived,
        )

    def to_full_dto(self) -> FormFullDTO:
        return FormFullDTO(
            id=self.id,
            created_at=self.created_at,
            last_modified_at=self.last_modified_at,
            created_by=self.created_by.to_dto(),
            last_modified_by=self.last_modified_by.to_dto(),
            name=self.name,
            template_version_id=self.template_version_id,
            status=self.status,
            submitted_at=self.submitted_at,
            submitted_by=self.submitted_by.to_dto() if self.submitted_by else None,
            is_archived=self.is_archived,
            values=self.values,
        )

    class Meta:
        table_name = "gws_form"
        is_table = True
