from peewee import BooleanField, CharField

from gws_core.core.classes.enum_field import EnumField
from gws_core.core.model.model import Model
from gws_core.core.utils.settings import Settings
from gws_core.lab.lab_dto import LabDTO, LabEnvironment, LabMode


class LabModel(Model):
    """Model representing a lab (local or external)."""

    lab_id: str = CharField(max_length=36)
    name: str = CharField()
    is_current_lab: bool = BooleanField(default=False)
    mode: LabMode = EnumField(choices=LabMode, null=True)
    environment: LabEnvironment = EnumField(choices=LabEnvironment, null=False)
    domain: str = CharField(null=True)
    space_id: str = CharField(null=True)
    space_name: str = CharField(null=True)

    class Meta:
        table_name = "gws_lab"
        is_table = True
        indexes = ((("lab_id", "mode"), True),)

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
        )

    @classmethod
    def get_or_create_current_lab(cls) -> "LabModel":
        """Get or create the current lab entry from Settings.

        Reads lab_id, lab_name and space info from Settings.
        Creates the row if it doesn't exist, updates name/space if they changed.
        """
        space = Settings.get_instance().get_space()

        lab_mode = Settings.get_lab_mode()

        lab_dto = LabDTO(
            id="",
            lab_id=Settings.get_lab_id(),
            name=Settings.get_lab_name(),
            is_current_lab=True,
            mode=lab_mode,
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

    def get_api_url(self) -> str:
        """Build the API URL for this lab from its domain and mode.

        Uses the prod or dev API sub-domain based on the lab's mode.
        """
        if not self.domain:
            raise ValueError("Cannot build API URL: lab domain is not set")
        if self.mode == LabMode.DEV:
            sub_domain = Settings.dev_api_sub_domain()
        else:
            sub_domain = Settings.prod_api_sub_domain()
        return f"https://{sub_domain}.{self.domain}"

    @classmethod
    def get_or_create_from_dto(cls, lab_dto: LabDTO) -> "LabModel":
        """Get or create a lab entry from a LabDTO.

        Looks up by (lab_id, mode). A single physical lab running in both
        prod and dev mode will have two separate rows.
        Creates the row if it doesn't exist, updates fields if they changed.
        """
        lab: LabModel = cls.get_by_lab_id_and_mode(lab_dto.lab_id, lab_dto.mode)

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
