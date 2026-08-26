"""i18n state for Reflex apps — a single shared state, accessed via ``get_state``.

:class:`I18nState` is a standalone ``rx.State`` (not a mixin). Other states do **not**
inherit it; they *compose* it by fetching it with ``await self.get_state(I18nState)``. This
gives a single source of truth for the active language across the whole app.

Two resolution entry points:

- Backend (event handlers, raised ``ReflexAppError``, logs): fetch the state and call
  its :meth:`I18nState.tr` — ``(await self.get_state(I18nState)).tr("key")`` — which returns
  a plain ``str`` using the shared ``lang``.
- UI (component tree): :func:`~gws_reflex_base.translate`, a reactive var backed by the
  :attr:`t` computed var below.

This module stays free of any ``gws_core`` import (virtual environment apps compatibility).
"""

from collections.abc import Mapping
from typing import Any

import reflex as rx

from .reflex_i18n import DEFAULT_LANG, get_translations, resolve


class I18nState(rx.State):
    """Shared state holding the active language and translation resolution.

    It is a single standalone state for the whole app. Access it from any other state with
    ``await self.get_state(I18nState)`` rather than inheriting it.

    Usage::

        from gws_reflex_base import I18nState, translate, register_translations

        register_translations({"fr": {...}, "en": {...}})

        class MyState(rx.State):
            @rx.event
            async def do_something(self):
                i18n = await self.get_state(I18nState)
                # backend: real string, using the shared language
                return rx.toast.success(i18n.tr("saved"))

        # in a component (reactive):
        rx.heading(translate("title"))
        rx.button("EN", on_click=lambda: I18nState.set_lang("en"))
    """

    # Active language. Defaults to the module default; switch it with ``set_lang``.
    lang: str = DEFAULT_LANG

    @rx.event
    def set_lang(self, lang: str) -> None:
        """Set the active language (call from the UI, e.g. a language toggle).

        Guards against a non-``str`` argument: when wired to a generic click trigger
        (e.g. ``rx.menu.item``) the browser event payload can leak in as the argument,
        which would corrupt ``lang`` and crash the ``t`` var on the next recompute
        (``get_translations`` hashes ``lang``). Ignore anything that is not a string.
        """
        if not isinstance(lang, str):
            return
        self.lang = lang

    @rx.var
    def t(self) -> dict[str, str]:
        """Reactive translation dictionary for the active language.

        Backs :func:`~gws_reflex_base.translate`. Indexing it in a component
        (``I18nState.t[key]``) stays reactive, so the UI re-renders on language change.
        """
        return get_translations(self.lang)

    def tr(self, key: str, data: Mapping[str, Any] | None = None) -> str:
        """Resolve a translation key to a real string, using the shared language.

        For backend use (event handlers, exceptions, logs). Not reactive — it returns a
        plain ``str``. Fetch the state first: ``(await self.get_state(I18nState)).tr(key)``.
        ``data`` fills ``{{placeholder}}`` markers.

        :param key: translation key
        :type key: str
        :param data: values to inject into ``{{placeholder}}`` markers
        :type data: Mapping[str, Any] | None
        :return: the translated (and interpolated) string, or ``key`` if not found
        :rtype: str
        """
        return resolve(key, self.lang, data)
