
from gws_core.core.model.base import Base


class Processable(Base):

    config_specs: dict = {}

    # Provided at the Class level automatically by the @ProcessDecorator
    _typing_name: str = None
    _human_name: str = None
    _short_description: str = None
