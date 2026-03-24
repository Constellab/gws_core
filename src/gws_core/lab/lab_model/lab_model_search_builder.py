from gws_core.core.classes.search_builder import SearchBuilder
from gws_core.lab.lab_model.lab_model import LabModel


class LabModelSearchBuilder(SearchBuilder):
    def __init__(self) -> None:
        super().__init__(LabModel, default_orders=[LabModel.name.asc()])
