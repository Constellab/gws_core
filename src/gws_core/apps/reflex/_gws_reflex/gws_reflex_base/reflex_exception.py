"""Exception used by the Reflex base module.

This module must stay free of any ``gws_core`` (or ``fastapi``) import: it is loaded
by virtual environment apps where ``gws_core`` is not installed. ``ReflexAppError``
is the gws_core-free counterpart of ``gws_core``'s ``BadRequestException``, so the same
error handling works in both normal and virtual environment apps.
"""

from typing import Literal

# Mode used to render the error in the interface (same values as gws_core ExceptionShowMode)
ReflexExceptionShowMode = Literal["error", "info"]


class ReflexAppError(Exception):
    """Expected exception raised by a Reflex app.

    This is the gws_core-free exception used inside ``gws_reflex_base`` so that the
    code works in virtual environment apps (where ``gws_core`` is not available).

    The app backend exception handler catches it to display a clean toast message
    instead of a generic error.
    """

    detail: str
    show_as: ReflexExceptionShowMode

    def __init__(self, detail: str, show_as: ReflexExceptionShowMode = "error") -> None:
        """
        :param detail: human readable message of the error, shown to the user
        :type detail: str
        :param show_as: how to render the error in the interface ("error" or "info"),
            defaults to "error"
        :type show_as: ReflexExceptionShowMode
        """
        super().__init__(detail)
        self.detail = detail
        self.show_as = show_as

    def __str__(self) -> str:
        return self.detail
