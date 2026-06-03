"""Lightweight internationalisation (i18n) for Reflex apps.

This module is intentionally dependency-free (no ``gws_core`` import) so it also works
in virtual environment apps, like the rest of ``gws_reflex_base``.

The design follows two access patterns, because Reflex has two very different worlds:

- **In the component tree (UI)**, text must update *reactively* when the user switches
  language. A plain function returning a ``str`` would freeze the value at compile time,
  so the lookup must flow through a state var. Use :func:`translate` which returns a
  reactive Reflex var (it indexes into the ``I18nState.t`` computed var).
- **In event handlers (toasts, raised exceptions, logs)**, you are in plain Python with
  the real ``lang`` value available on ``self``. There, reactivity is irrelevant and you
  want a real ``str``. Use ``self.tr("key")`` from ``I18nState`` (Option A).

Apps register their own translation dictionaries with :func:`register_translations`
(``gws_reflex_base`` cannot know app-specific strings). A translation dictionary maps a
language code to a flat ``{key: text}`` dict::

    register_translations({
        "fr": {"title": "Investir", "greeting": "Bonjour {{name}}"},
        "en": {"title": "Invest",   "greeting": "Hello {{name}}"},
    })

Texts may contain ``{{placeholder}}`` markers, filled by passing a ``data`` dict:
``resolve("greeting", "en", {"name": "world"}) -> "Hello world"``.

Keys are resolved by language with a fallback to :data:`DEFAULT_LANG`, and finally to the
key itself (so a missing translation renders the key rather than crashing).
"""

import re
from collections.abc import Mapping
from typing import Any

# Default language used both as the initial value and as the fallback when a key is
# missing in the requested language.
DEFAULT_LANG: str = "fr"

# Languages offered by the built-in language toggle, in display order. Each entry is a
# (code, label) pair. Apps can override the list passed to ``language_toggle_component``.
SUPPORTED_LANGS: list[tuple[str, str]] = [("fr", "FR"), ("en", "EN")]

# Module-level registry of translations: ``{lang: {key: text}}``. Apps populate this at
# import time via ``register_translations``. It is a process-global on purpose: a Reflex
# app process serves a single app, so there is no cross-app collision concern.
_TRANSLATIONS: dict[str, dict[str, str]] = {}

# Matches ``{{ name }}`` placeholders (optional surrounding whitespace).
_PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def register_translations(translations: dict[str, dict[str, str]]) -> None:
    """Register (merge) an app's translation dictionaries.

    Calling it several times merges the dictionaries, so an app may split its strings
    across modules and register each part independently.

    :param translations: mapping of language code to a flat ``{key: text}`` dictionary
    :type translations: dict[str, dict[str, str]]
    """
    for lang, entries in translations.items():
        _TRANSLATIONS.setdefault(lang, {}).update(entries)


def get_translations(lang: str) -> dict[str, str]:
    """Return the flat ``{key: text}`` dictionary for a language.

    Falls back to :data:`DEFAULT_LANG`, then to an empty dict if nothing is registered.

    :param lang: language code (e.g. ``"fr"`` or ``"en"``)
    :type lang: str
    :return: the translation dictionary for the language
    :rtype: dict[str, str]
    """
    return _TRANSLATIONS.get(lang) or _TRANSLATIONS.get(DEFAULT_LANG) or {}


def interpolate(text: str, data: Mapping[str, Any] | None) -> str:
    """Fill ``{{placeholder}}`` markers in ``text`` from ``data``.

    Unknown placeholders are left untouched (so a missing value is visible but does not
    crash). Returns ``text`` unchanged when ``data`` is falsy.

    :param text: the raw text, possibly containing ``{{key}}`` markers
    :type text: str
    :param data: values to inject, keyed by placeholder name
    :type data: Mapping[str, Any] | None
    :return: the interpolated text
    :rtype: str
    """
    if not data:
        return text

    def _sub(match: "re.Match[str]") -> str:
        name = match.group(1)
        return str(data[name]) if name in data else match.group(0)

    return _PLACEHOLDER_RE.sub(_sub, text)


def resolve(key: str, lang: str, data: Mapping[str, Any] | None = None) -> str:
    """Resolve a translation key to a real string for a given language.

    This is the plain-Python resolver used by the backend (event handlers). It tries the
    requested language, then :data:`DEFAULT_LANG`, then returns the key itself so a
    missing translation is visible but never crashes. ``{{placeholder}}`` markers in the
    resolved text are filled from ``data``.

    :param key: translation key
    :type key: str
    :param lang: language code
    :type lang: str
    :param data: values to inject into ``{{placeholder}}`` markers
    :type data: Mapping[str, Any] | None
    :return: the translated (and interpolated) string, or ``key`` if not found
    :rtype: str
    """
    entries = _TRANSLATIONS.get(lang) or {}
    if key in entries:
        return interpolate(entries[key], data)
    fallback = _TRANSLATIONS.get(DEFAULT_LANG) or {}
    return interpolate(fallback.get(key, key), data)
