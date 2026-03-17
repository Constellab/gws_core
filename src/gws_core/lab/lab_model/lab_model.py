from peewee import BooleanField, CharField, ForeignKeyField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException
from gws_core.core.exception.gws_exceptions import GWSException
from gws_core.core.model.model import Model
from gws_core.core.utils.settings import Settings
from gws_core.credentials.credentials import Credentials
from gws_core.lab.lab_model.lab_dto import LabDTO, LabDTOWithCredentials
from gws_core.lab.lab_model.lab_enums import LabEnvironment, LabMode


class LabModel(Model):
    """Model representing a lab (local or external)."""

    lab_id: str = CharField(max_length=36)
    name: str = CharField()
    is_current_lab: bool = BooleanField(default=False)
    mode: LabMode = EnumField(choices=LabMode, null=False)
    environment: LabEnvironment = EnumField(choices=LabEnvironment, null=False)
    domain: str | None = CharField(null=True)
    space_id: str | None = CharField(null=True)
    space_name: str | None = CharField(null=True)
    credentials: Credentials | None = ForeignKeyField(
        Credentials, null=True, index=True, backref="+"
    )

    class Meta:
        table_name = "gws_lab"
        is_table = True
        indexes = ((("lab_id", "mode"), True),)

    def has_credentials(self) -> bool:
        """Check if the lab has credentials data."""
        return self.credentials is not None and self.credentials.get_data_object() is not None

    def check_credentials_and_domain(self) -> None:
        """Check that the lab has credentials and domain configured for external communication."""
        if not self.domain:
            raise BadRequestException(
                GWSException.LAB_MISSING_CREDENTIALS_OR_DOMAIN.value, {"lab_name": self.name}
            )
        if not self.has_credentials():
            raise BadRequestException(
                GWSException.LAB_MISSING_CREDENTIALS_OR_DOMAIN.value, {"lab_name": self.name}
            )

    def to_dto(self) -> LabDTO:
        """Convert the model to a DTO."""
        return LabDTO(
            id=self.id,
            lab_id=self.lab_id,
            name=self.name,
            is_current_lab=self.is_current_lab,
            mode=self.mode,
            environment=self.environment,
            domain=self.domain,
            space_id=self.space_id,
            space_name=self.space_name,
            credentials_id=self.credentials.id if self.credentials else None,
        )

    def to_dto_with_credentials(self) -> LabDTOWithCredentials:
        """Convert the model to a DTO with resolved credentials data."""
        credentials_data = None
        if self.credentials:
            credentials_data = self.credentials.get_data_object()
        return LabDTOWithCredentials(
            id=self.id,
            lab_id=self.lab_id,
            name=self.name,
            is_current_lab=self.is_current_lab,
            mode=self.mode,
            environment=self.environment,
            domain=self.domain,
            space_id=self.space_id,
            space_name=self.space_name,
            credentials_id=self.credentials.id if self.credentials else None,
            credentials_data=credentials_data,
        )

    @classmethod
    def get_or_create_current_lab(cls) -> "LabModel":
        """Get or create the current lab entry from Settings.

        Reads lab_id, lab_name and space info from Settings.
        Creates the row if it doesn't exist, updates name/space if they changed.
        """
        space = Settings.get_instance().get_space()

        lab_dto = LabDTO(
            id="",
            lab_id=Settings.get_lab_id(),
            name=Settings.get_lab_name(),
            is_current_lab=True,
            mode=Settings.get_lab_mode(),
            environment=Settings.get_lab_environment(),
            domain=Settings.get_virtual_host(),
            space_id=space["id"] if space else None,
            space_name=space["name"] if space else None,
        )

        return cls.get_or_create_from_dto(lab_dto)

    @classmethod
    def get_by_lab_id_and_mode(cls, lab_id: str, mode: LabMode | None) -> "LabModel | None":
        """Get a lab entry by its logical lab_id and mode."""
        return cls.get_or_none((cls.lab_id == lab_id) & (cls.mode == mode))

    @classmethod
    def get_or_create_from_dto(cls, lab_dto: LabDTO) -> "LabModel":
        """Get or create a lab entry from a LabDTO.

        Looks up by (lab_id, mode). A single physical lab running in both
        prod and dev mode will have two separate rows.
        Creates the row if it doesn't exist, updates fields if they changed.
        """
        lab = cls.get_by_lab_id_and_mode(lab_dto.lab_id, lab_dto.mode)

        if lab is None:
            lab = cls()
            lab.lab_id = lab_dto.lab_id
            lab.name = lab_dto.name
            lab.is_current_lab = lab_dto.is_current_lab
            lab.mode = lab_dto.mode
            lab.environment = lab_dto.environment
            lab.domain = lab_dto.domain
            lab.space_id = lab_dto.space_id
            lab.space_name = lab_dto.space_name
            lab.save(force_insert=True)
        else:
            updated = False
            if lab.name != lab_dto.name:
                lab.name = lab_dto.name
                updated = True
            if lab.is_current_lab != lab_dto.is_current_lab:
                lab.is_current_lab = lab_dto.is_current_lab
                updated = True
            if lab.environment != lab_dto.environment:
                lab.environment = lab_dto.environment
                updated = True
            if lab.domain != lab_dto.domain:
                lab.domain = lab_dto.domain
                updated = True
            if lab.space_id != lab_dto.space_id:
                lab.space_id = lab_dto.space_id
                updated = True
            if lab.space_name != lab_dto.space_name:
                lab.space_name = lab_dto.space_name
                updated = True
            if updated:
                lab.save()

        return lab

    @classmethod
    def get_current_lab(cls) -> "LabModel | None":
        """Get the current lab entry for the current mode, or None if not yet created."""
        return cls.get_or_none((cls.is_current_lab == True) & (cls.mode == Settings.get_lab_mode()))
