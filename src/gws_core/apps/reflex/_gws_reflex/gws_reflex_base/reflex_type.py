# Define a generic type variable
from typing import Awaitable, Callable, TypeVar

T = TypeVar('T')

# Define the generic callable type
ReflexDialogCloseEvent = Callable[[T], Awaitable[None]]
