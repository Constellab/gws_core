# Define a generic type variable
from collections.abc import Awaitable, Callable
from typing import TypeVar

T = TypeVar("T")

# Define the generic callable type
ReflexDialogCloseEvent = Callable[[T], Awaitable[None]]
