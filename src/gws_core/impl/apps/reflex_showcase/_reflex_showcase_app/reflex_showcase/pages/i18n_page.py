"""Internationalisation (i18n) demo page for the Reflex showcase app.

Demonstrates the i18n layer from ``gws_reflex_base`` (re-exported by ``gws_reflex_main``):
the reactive ``translate`` UI helper, the ``toast_tr`` translating toasts, placeholder
interpolation, the ``language_toggle_component``, and the standalone ``I18nState`` accessed
from another state via ``get_state``.

Only this page is translated — the rest of the showcase stays single-language.
"""

import reflex as rx
from gws_reflex_main import (
    I18nState,
    language_toggle_component,
    register_translations,
    toast_tr,
    translate,
)

from ..components import example_tabs, page_layout

# Page-scoped translation keys. Apps register their own strings; ``register_translations``
# merges, so this page's keys live alongside any other registered translations.
register_translations(
    {
        "fr": {
            "i18n_demo_heading": "Bonjour 👋",
            "i18n_demo_text": "Ce texte change de langue instantanément.",
            "i18n_greeting": "Bienvenue, {{name}} !",
            "i18n_saved": "Modifications enregistrées",
            "i18n_deleted": "Élément « {{item}} » supprimé",
            "i18n_name_label": "Votre nom",
            "i18n_toast_success_btn": "Toast succès",
            "i18n_toast_error_btn": "Toast erreur (avec donnée)",
        },
        "en": {
            "i18n_demo_heading": "Hello 👋",
            "i18n_demo_text": "This text switches language instantly.",
            "i18n_greeting": "Welcome, {{name}}!",
            "i18n_saved": "Changes saved",
            "i18n_deleted": 'Item "{{item}}" deleted',
            "i18n_name_label": "Your name",
            "i18n_toast_success_btn": "Success toast",
            "i18n_toast_error_btn": "Error toast (with data)",
        },
    }
)


class I18nDemoState(rx.State):
    """Demo state — does NOT inherit ``I18nState``; it composes it via ``get_state``."""

    name: str = "Ada"

    @rx.event
    def set_name(self, value: str):
        self.name = value

    @rx.event
    async def show_success(self):
        # Translating toast: pass ``self`` so toast_tr can read the shared language and
        # resolve the message to a plain string server-side.
        yield await toast_tr.success(self, "i18n_saved")

    @rx.event
    async def show_error_with_data(self):
        # ``data`` fills the ``{{item}}`` placeholder.
        yield await toast_tr.error(self, "i18n_deleted", {"item": "Sample"}, duration=4000)

    @rx.event
    async def show_current_language(self):
        # Backend access to the shared language / raw string via the standalone state
        # (composed with get_state, not inherited). ``tr`` returns a plain str.
        i18n = await self.get_state(I18nState)
        yield rx.toast.info(f"lang={i18n.lang} · tr='{i18n.tr('i18n_saved')}'")


def i18n_page() -> rx.Component:
    """Render the i18n demo page."""

    # ---- Example 1: reactive translation + language toggle ---------------
    example1 = rx.vstack(
        language_toggle_component(),
        rx.heading(translate("i18n_demo_heading"), size="6"),
        rx.text(translate("i18n_demo_text")),
        rx.callout(
            translate("i18n_demo_text"),
            icon="languages",
        ),
        spacing="3",
        align="start",
        width="100%",
    )

    code1 = """from gws_reflex_main import translate, language_toggle_component, register_translations

register_translations({
    "fr": {"hello": "Bonjour 👋"},
    "en": {"hello": "Hello 👋"},
})

# In a component — translate() is reactive: the text re-renders on language change.
rx.heading(translate("hello"))
language_toggle_component()   # built-in FR/EN switcher (reads/sets the shared I18nState)"""

    # ---- Example 2: placeholder interpolation ----------------------------
    example2 = rx.vstack(
        language_toggle_component(),
        rx.text(translate("i18n_name_label")),
        rx.input(
            value=I18nDemoState.name,
            on_change=I18nDemoState.set_name,
            width="100%",
        ),
        rx.heading(translate("i18n_greeting", {"name": I18nDemoState.name}), size="5"),
        spacing="3",
        align="start",
        width="100%",
    )

    code2 = """# Texts may contain {{placeholder}} markers, filled from a data dict.
register_translations({
    "fr": {"greeting": "Bienvenue, {{name}} !"},
    "en": {"greeting": "Welcome, {{name}}!"},
})

# data values may be plain values OR reactive vars (here a state var):
rx.heading(translate("greeting", {"name": MyState.name}))"""

    # ---- Example 3: translating toasts (toast_tr) ------------------------
    example3 = rx.vstack(
        language_toggle_component(),
        rx.hstack(
            rx.button(
                translate("i18n_toast_success_btn"),
                on_click=I18nDemoState.show_success,
            ),
            rx.button(
                translate("i18n_toast_error_btn"),
                on_click=I18nDemoState.show_error_with_data,
                color_scheme="red",
            ),
            rx.button(
                "tr() via get_state",
                on_click=I18nDemoState.show_current_language,
                variant="soft",
            ),
            spacing="3",
        ),
        rx.text(translate("i18n_demo_text"), size="2", color="gray"),
        spacing="3",
        align="start",
        width="100%",
    )

    code3 = """from gws_reflex_main import toast_tr

class MyState(rx.State):
    @rx.event
    async def save(self):
        # toast_tr mirrors rx.toast (callable + .success/.error/.info/.warning) but is async
        # and takes the calling state first, so it resolves the message server-side.
        yield await toast_tr.success(self, "saved")
        yield await toast_tr.error(self, "deleted", {"item": name}, duration=4000)

    @rx.event
    async def need_raw_string(self):
        # For a raw str (e.g. an exception message) compose the shared state:
        i18n = await self.get_state(I18nState)
        msg = i18n.tr("saved")   # plain str, uses the shared language"""

    return page_layout(
        "Internationalisation (i18n)",
        "Demonstrates the i18n layer: reactive translate(), translating toast_tr toasts, "
        "{{placeholder}} interpolation, and the language toggle. Switch FR/EN with the toggle "
        "in each example and watch the text update live.",
        example_tabs(
            example_component=example1,
            code=code1,
            title="translate() + language_toggle_component()",
            description="translate(key) returns a reactive var, so UI text switches language "
            "instantly. language_toggle_component() reads/sets the shared I18nState.",
            func=translate,
        ),
        example_tabs(
            example_component=example2,
            code=code2,
            title="Placeholder interpolation",
            description="Texts with {{name}} markers are filled from a data dict; values may "
            "be plain values or reactive vars.",
        ),
        example_tabs(
            example_component=example3,
            code=code3,
            title="toast_tr — translating toasts",
            description="toast_tr mirrors rx.toast (callable + .success/.error/.info/.warning), "
            "but is async and takes the calling state first so it resolves the message "
            "server-side. The last button shows get_state(I18nState).tr(key) for a raw string.",
        ),
    )
