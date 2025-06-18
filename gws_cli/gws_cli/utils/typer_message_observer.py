

from typing import List

import typer

from gws_core import DispatchedMessage, MessageObserver


class TyperMessageObserver(MessageObserver):
    """Observer to log dispatched message to the logger"""

    def update(self, messages: List[DispatchedMessage]) -> None:
        for message in messages:
            typer.echo(f"{message.status.value}: {message.message}")
