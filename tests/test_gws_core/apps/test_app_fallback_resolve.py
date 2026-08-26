import asyncio
import os
import sys
from collections.abc import Callable, Coroutine
from typing import Any, cast

from gws_core import BaseTestCase
from gws_core.apps import app_gateway_constants
from gws_core.apps.app_gateway_service import AppGatewayService
from gws_core.apps.app_nginx_manager import AppNginxManager
from gws_core.apps.reflex import reflex_process
from gws_core.apps.reflex.reflex_process import ReflexProcess
from reflex.istate.data import HeaderData, ReflexURL

# gws_reflex_base ships as a standalone package for app processes (it must not import gws_core), so
# it is not reachable as gws_core.*: put its folder on the path exactly as ReflexProcess does for a
# spawned app.
sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(reflex_process.__file__)),
        ReflexProcess.REFLEX_MODULES_PATH,
    ),
)

from gws_reflex_base.reflex_main_state_base import ReflexMainStateBase  # noqa: E402

# `on_main_component_mount` is decorated with `@rx.event`, so on the class it is an EventCallback
# descriptor rather than the coroutine function. Calling it unbound is what these tests need, so go
# through the real callable.
_on_main_component_mount = cast(
    Callable[[object], Coroutine[Any, Any, object]],
    ReflexMainStateBase.on_main_component_mount,
)


class _FakeMainState:
    """Stand-in for the state hosting the ReflexMainStateBase mixin.

    `on_main_component_mount` is tested unbound: a real `rx.State` instance needs a running Reflex
    app, while the invariant under test is purely about what the handler does with `_on_load`'s
    result.
    """

    def __init__(self, on_load_result, initializes: bool = False) -> None:
        self._on_load_result = on_load_result
        self._initializes = initializes
        self._is_initialized = False
        self.main_component_initialized = False

    async def _on_load(self):
        if self._initializes:
            self._is_initialized = True
        return self._on_load_result


class TestAppFallbackResolve(BaseTestCase):
    """Tests for the nginx fallback that keeps a shared app URL working when the app is stopped.

    An app's nginx block only exists while it runs, so such a URL matches no server block. The
    fallback `default_server` block routes it to the resolver, which maps the host back to an app
    key and redirects to the Angular gateway (auth guard + cold-start + progress UI).
    """

    def test_app_key_from_host_local(self):
        """A local app host resolves to its middle segment (the app key)."""
        self.assertEqual(AppGatewayService.app_key_from_host("abc123.localhost"), "abc123")

    def test_app_key_from_host_ignores_port(self):
        """The port is not part of the app key.

        Load-bearing for the in-app gateway re-entry: the Reflex app sends `router.url.netloc`,
        which includes the port (ReflexURL exposes no port-less host attribute).
        """
        self.assertEqual(AppGatewayService.app_key_from_host("abc123.localhost:8510"), "abc123")

    def test_reflex_url_exposes_netloc_not_host(self):
        """Pin the ReflexURL attribute the in-app redirect relies on.

        `_redirect_to_gateway` reads `router.url.netloc`; an earlier version read `.host`, which does
        not exist and raised at runtime ("'ReflexURL' object has no attribute 'host'"). This fails if
        a Reflex upgrade renames it.
        """
        url = ReflexURL("http://abc123.localhost:8510/config?tab=1")

        self.assertEqual(url.netloc, "abc123.localhost:8510")
        self.assertEqual(url.path, "/config")
        self.assertEqual(url.query, "tab=1")
        self.assertFalse(hasattr(url, "host"))

    def test_reflex_header_data_exposes_a_populated_host(self):
        """Pin the HeaderData attribute the host resolution falls back to.

        `_resolve_request_host` prefers `router.url.netloc` and falls back to
        `router.headers.host` when the request carried no `Origin` (the URL is then path-only, so
        netloc is empty). Header names are case-insensitive on the wire; Reflex snake-cases them
        into the typed field. This fails if a Reflex upgrade drops or renames it.
        """
        headers = HeaderData.from_router_data(
            {"headers": {"Host": "abc123.localhost:8510", "origin": "http://abc123.localhost:8510"}}
        )

        self.assertEqual(headers.host, "abc123.localhost:8510")
        # the port is kept: app_key_from_host strips it (see test above)
        self.assertEqual(HeaderData.from_router_data({}).host, "")

    def test_on_main_component_mount_returns_the_redirect(self):
        """The gateway redirect must be handed back to Reflex, not swallowed.

        This is the bug that made a direct app URL in a private browser fail instead of bouncing:
        `rx.redirect` only builds an `EventSpec`, and the mount handler used to `await _on_load()`
        without returning its result, so the browser was never told to navigate.
        """
        redirect = object()
        state = _FakeMainState(on_load_result=redirect)

        result = asyncio.run(_on_main_component_mount(state))

        self.assertIs(result, redirect)
        # the page is leaving: rendering the app content to an unauthenticated visitor is not allowed
        self.assertFalse(state.main_component_initialized)

    def test_on_main_component_mount_waits_when_load_checked_nothing(self):
        """A load that bailed out early (router not ready) must not unlock the app content.

        `_on_load` returns None both when initialization succeeded and when it skipped every check,
        so the flag follows `_is_initialized` rather than the return value.
        """
        state = _FakeMainState(on_load_result=None, initializes=False)

        self.assertIsNone(asyncio.run(_on_main_component_mount(state)))
        self.assertFalse(state.main_component_initialized)

    def test_on_main_component_mount_initializes_after_a_successful_load(self):
        """The normal path still flips the flag that reveals the app content."""
        state = _FakeMainState(on_load_result=None, initializes=True)

        self.assertIsNone(asyncio.run(_on_main_component_mount(state)))
        self.assertTrue(state.main_component_initialized)

    def test_app_key_from_host_strips_reflex_back_suffix(self):
        """A Reflex app's front and backend hosts resolve to the same app."""
        self.assertEqual(AppGatewayService.app_key_from_host("abc123-back.localhost"), "abc123")

    def test_app_key_from_host_is_case_insensitive(self):
        """Host names are case-insensitive; ids/subdomains are stored lowercase."""
        self.assertEqual(AppGatewayService.app_key_from_host("ABC123.localhost"), "abc123")

    def test_app_key_from_host_rejects_non_app_hosts(self):
        """A host that is not shaped like an app host yields no key (caller renders a 404)."""
        for host in ["notanapphost.com", "", ".localhost", "localhost"]:
            self.assertIsNone(AppGatewayService.app_key_from_host(host), f"host={host!r}")

    def test_build_fallback_redirect_url_invalid_host_returns_error_url(self):
        """A host that is not an app host redirects to the gateway error page, never raises.

        The resolver is reached by a top-level browser navigation, so raising an API exception would
        show the raw JSON error envelope to a human.
        """
        url = AppGatewayService.build_fallback_redirect_url("notanapphost.com", None)

        self.assertIn(f"error={app_gateway_constants.GATEWAY_ERROR_INVALID_HOST}", url)
        # no app key: the page must not try to open (or start) anything
        self.assertNotIn("notanapphost", url)

    def test_build_fallback_redirect_url_unknown_app_returns_error_url(self):
        """A well-shaped host whose key matches no app also redirects to the error page."""
        url = AppGatewayService.build_fallback_redirect_url("no-such-app-id.localhost", None)

        self.assertIn(f"error={app_gateway_constants.GATEWAY_ERROR_APP_NOT_FOUND}", url)
        self.assertNotIn("no-such-app-id", url)

    def test_sanitize_redirect_target_keeps_in_app_path(self):
        """A plain in-app path is preserved so a shared deep link is not lost."""
        self.assertEqual(AppGatewayService._sanitize_redirect_target("/config?a=1"), "/config?a=1")

    def test_sanitize_redirect_target_rejects_off_origin(self):
        """Anything that could leave the app origin is dropped (open-redirect guard)."""
        for target in ["//evil.com", "https://evil.com", "config", None, ""]:
            self.assertIsNone(AppGatewayService._sanitize_redirect_target(target), f"t={target!r}")

    def test_sanitize_redirect_target_rejects_fallback_path(self):
        """The fallback path itself is dropped, otherwise the redirect could loop."""
        target = f"/{app_gateway_constants.APP_FALLBACK_PATH}?host=x"
        self.assertIsNone(AppGatewayService._sanitize_redirect_target(target))

    def test_init_starts_nginx_with_the_fallback(self):
        """Lab boot must leave nginx *running* with the fallback block.

        `init` used to stop nginx at boot, and nothing restarted it until the first app launched --
        so a shared URL of a stopped app hit a dead port for the whole idle period. Guard that the
        boot path ends in a start/reload rather than a stop.
        """
        manager = AppNginxManager()
        calls: list[str] = []
        manager.nginx_is_running = lambda: False  # type: ignore[method-assign]
        manager.stop = lambda force=False: calls.append("stop")  # type: ignore[method-assign]
        manager.start_or_reload = lambda: calls.append("start_or_reload")  # type: ignore[method-assign]

        AppNginxManager._instance = manager
        try:
            AppNginxManager.init()
        finally:
            AppNginxManager._instance = None

        self.assertEqual(calls, ["start_or_reload"])

    def test_init_survives_a_failing_nginx_start(self):
        """Boot must not die when the app port is already served by another process.

        A concurrently running lab server (or an nginx owning a different PID file) already holds
        the port; apps still work in that case, so the fallback failing to bind must not take the
        whole lab boot down.
        """
        manager = AppNginxManager()

        def _raise() -> None:
            raise Exception("bind() to 0.0.0.0:8510 failed")

        manager.nginx_is_running = lambda: False  # type: ignore[method-assign]
        manager.start_or_reload = _raise  # type: ignore[method-assign]

        AppNginxManager._instance = manager
        try:
            AppNginxManager.init()  # must not raise
        finally:
            AppNginxManager._instance = None

    def test_nginx_config_contains_fallback_with_no_services(self):
        """The fallback block must render even with zero registered apps.

        This is the regression guard for the two bugs that made a stopped app's URL dead: the
        config builder used to short-circuit to a bare comment when no services were registered,
        and unregistering the last service stopped nginx altogether.
        """
        manager = AppNginxManager()
        config = manager._build_nginx_config()

        self.assertIn("default_server", config)
        self.assertIn(app_gateway_constants.APP_FALLBACK_PATH, config)
        # the resolver upstream must be a literal loopback IP: a hostname or any $var in
        # proxy_pass forces runtime DNS resolution nginx is not configured for
        self.assertNotIn("proxy_pass http://localhost", config)
