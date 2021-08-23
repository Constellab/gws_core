

from ..config.config_spec import ConfigSpecs
from ..core.model.base import Base


class Processable(Base):

    config_specs: ConfigSpecs = {}

    # Provided at the Class level automatically by the Decorator
    # //!\\ Do not modify theses values
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
