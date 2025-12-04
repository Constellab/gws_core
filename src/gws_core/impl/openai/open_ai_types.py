from typing import List, Literal, Optional

import plotly.graph_objs as go
from pandas import DataFrame
from typing_extensions import TypedDict

from gws_core.core.model.model_dto import BaseModelDTO


class OpenAiChatMessage(TypedDict):
    """Format of the message for OpenAI chat

    :param TypedDict: _description_
    :type TypedDict: _type_
    """

    role: Literal["system", "user", "assistant"]
    content: str


class OpenAiChatDict(TypedDict):
    """Format of the chat for OpenAI chat

    :param TypedDict: _description_
    :type TypedDict: _type_
    """

    messages: List[OpenAiChatMessage]


class AiChatMessageAdditionalInfo(BaseModelDTO):
    dataframes: Optional[List[DataFrame]] = None
    plots: Optional[List[go.Figure]] = None

    class Config:
        arbitrary_types_allowed = True


class AiChatMessage(BaseModelDTO):
    """Overload of OpenAiChatMessage to add custom info (not sent to OpenAI)
    but stored in the chat object
    """

    role: Literal["system", "user", "assistant"]
    content: str
    user_id: Optional[str] = None
    additional_info: Optional[AiChatMessageAdditionalInfo] = None

    def is_user(self) -> bool:
        return self.role == "user"

    def add_plot(self, plot: go.Figure) -> None:
        if self.additional_info is None:
            self.additional_info = AiChatMessageAdditionalInfo()
        if self.additional_info.plots is None:
            self.additional_info.plots = []
        self.additional_info.plots.append(plot)

    def add_dataframe(self, dataframe: DataFrame) -> None:
        if self.additional_info is None:
            self.additional_info = AiChatMessageAdditionalInfo()
        if self.additional_info.dataframes is None:
            self.additional_info.dataframes = []
        self.additional_info.dataframes.append(dataframe)

    def get_plots(self) -> List[go.Figure] | None:
        if self.additional_info is None:
            return None
        return self.additional_info.plots

    def get_dataframes(self) -> List[DataFrame] | None:
        if self.additional_info is None:
            return None
        return self.additional_info.dataframes
