"""UI helpers for the i18n layer: reactive ``translate``, translating toasts, language toggle.

``translate`` returns a reactive var for the component tree. ``toast_tr`` produces a toast
whose message is resolved to a plain string server-side (it cannot be a reactive var: a toast
yielded from an event handler is applied client-side in a scope that can't resolve a
cross-state var reference). ``toast_tr`` therefore takes the calling state as its first
argument and reads the shared language via ``get_state``::

    from gws_reflex_base import translate, toast_tr, language_toggle_component

    rx.heading(translate("title"))                  # reactive text
    yield await toast_tr.success(self, "saved")     # translating toast (in an event handler)
    language_toggle_component()                     # language switcher

This module stays free of any ``gws_core`` import (virtual environment apps compatibility).
"""

from collections.abc import Mapping
from typing import Any

import reflex as rx

from .reflex_i18n import SUPPORTED_LANGS
from .reflex_i18n_state import I18nState


def translate(key: str, data: Mapping[str, Any] | None = None):
    """Return a *reactive* translation for use in the component tree (UI).

    The returned value is a Reflex var (an index into :attr:`I18nState.t`), so the rendered
    text updates automatically when the language changes. Use this only inside components,
    never in event handlers (use ``(await self.get_state(I18nState)).tr(key)`` there).

    ``{{placeholder}}`` markers are filled from ``data`` using reactive string replacement,
    so values may themselves be Reflex vars (e.g. ``translate("greeting", {"name": MyState.user})``).

    Example::

        rx.heading(translate("title"))
        rx.text(translate("greeting", {"name": "world"}))

    :param key: translation key
    :type key: str
    :param data: values to inject into ``{{placeholder}}`` markers (plain values or vars)
    :type data: Mapping[str, Any] | None
    :return: a reactive Reflex var resolving to the translated text
    """
    text = I18nState.t[key]
    if data:
        # Reflex string vars support ``.replace``; chain one per placeholder so the result
        # stays reactive even when a value is itself a var. Reflex's ``.replace`` requires a
        # string operand, so coerce plain non-string values (a var is passed through as-is).
        for name, value in data.items():
            replacement = value if isinstance(value, rx.Var) else str(value)
            text = text.replace("{{" + name + "}}", replacement).replace(
                "{{ " + name + " }}", replacement
            )
    return text


class _ToastTr:
    """Translating counterpart of ``rx.toast``, mirroring its callable + variants API.

    The toast message is resolved to a **plain string** server-side using the shared language,
    so it can be safely applied client-side (a reactive cross-state var cannot — it would not
    resolve in the toast's client event-apply scope). Each method is ``async`` and takes the
    calling ``state`` as its first argument to reach :class:`I18nState` via ``get_state``; it
    returns a Reflex toast ``EventSpec`` to ``yield``/``return`` from an event handler::

        yield await toast_tr(self, "saved")                # default toast
        yield await toast_tr.success(self, "saved")
        yield await toast_tr.error(self, "invalid_email", {"email": value}, duration=5000)

    ``data`` fills ``{{placeholder}}`` markers; extra kwargs (``description``, ``duration``,
    ...) are forwarded to the underlying ``rx.toast.*`` call.
    """

    @staticmethod
    async def _toast(
        level: str, state: rx.State, key: str, data: Mapping[str, Any] | None, kwargs: dict
    ):
        i18n = await state.get_state(I18nState)
        message = i18n.tr(key, data)  # plain str, resolved with the shared language
        toast_fn = rx.toast if level == "default" else getattr(rx.toast, level)
        return toast_fn(message, **kwargs)

    async def __call__(
        self, state: rx.State, key: str, data: Mapping[str, Any] | None = None, **kwargs
    ):
        """Translating default toast (mirrors ``rx.toast(...)``)."""
        return await self._toast("default", state, key, data, kwargs)

    async def success(
        self, state: rx.State, key: str, data: Mapping[str, Any] | None = None, **kwargs
    ):
        """Translating success toast (mirrors ``rx.toast.success(...)``)."""
        return await self._toast("success", state, key, data, kwargs)

    async def error(
        self, state: rx.State, key: str, data: Mapping[str, Any] | None = None, **kwargs
    ):
        """Translating error toast (mirrors ``rx.toast.error(...)``)."""
        return await self._toast("error", state, key, data, kwargs)

    async def info(
        self, state: rx.State, key: str, data: Mapping[str, Any] | None = None, **kwargs
    ):
        """Translating info toast (mirrors ``rx.toast.info(...)``)."""
        return await self._toast("info", state, key, data, kwargs)

    async def warning(
        self, state: rx.State, key: str, data: Mapping[str, Any] | None = None, **kwargs
    ):
        """Translating warning toast (mirrors ``rx.toast.warning(...)``)."""
        return await self._toast("warning", state, key, data, kwargs)


# Singleton exposing the ``rx.toast``-style API: ``toast_tr(self, ...)``, ``toast_tr.success(self, ...)``.
toast_tr = _ToastTr()


def language_toggle_component(
    languages: list[tuple[str, str]] | None = None,
    size: str = "1",
    **kwargs,
) -> rx.Component:
    """Render a segmented control to switch the active language.

    Reads and updates the shared :class:`I18nState` directly.

    :param languages: ordered ``(code, label)`` pairs to offer; defaults to
        :data:`~gws_reflex_base.reflex_i18n.SUPPORTED_LANGS` (``[("fr", "FR"), ("en", "EN")]``)
    :type languages: list[tuple[str, str]] | None
    :param size: segmented control size ("1", "2" or "3"), defaults to "1"
    :type size: str
    :param kwargs: extra props forwarded to ``rx.segmented_control.root``
    :return: the language toggle component
    :rtype: rx.Component
    """
    langs = languages or SUPPORTED_LANGS
    return rx.segmented_control.root(
        *[
            rx.segmented_control.item(label, value=code)
            for code, label in langs
        ],
        value=I18nState.lang,
        # segmented_control emits the selected value; forward it explicitly to set_lang.
        on_change=lambda value: I18nState.set_lang(value),
        size=size,
        **kwargs,
    )
