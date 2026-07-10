from unittest import TestCase

from fastapi import FastAPI
from gws_core.core.classes.cors_config import CorsConfig, CorsPolicy
from gws_core.lab.api_registry import ApiRegistry
from starlette.testclient import TestClient

LAB_ORIGIN = "https://app.mylab.io"
THIRD_PARTY_ORIGIN = "https://third-party.example"


# test_cors_config
class TestCorsConfig(TestCase):
    """Test the per-sub-app CORS and security-headers topology.

    Reproduces what ``App`` builds: a main app with NO CORS or security-headers
    middleware, sub-apps registered through ``ApiRegistry`` (one keeping the lab
    default CORS, one declaring its own ``CorsPolicy``, one opting out of
    security headers) — each getting its own middlewares at registration — then
    mounted. The lab origin regex is pinned to a fake cloud virtual host so the
    default policy discriminates; the pin works because
    ``LabDefaultCorsMiddleware`` resolves it lazily, on the app's first request.
    """

    client: TestClient

    @classmethod
    def setUpClass(cls) -> None:
        # Snapshot the global state touched by the test, restored in tearDownClass
        cls._saved_apis = dict(ApiRegistry._apis)
        cls._saved_silent_paths = list(ApiRegistry._silent_paths)
        cls._saved_origin_regex = CorsConfig._get_allow_origin_regex

        ApiRegistry.clear()
        main_app = FastAPI(docs_url=None)

        default_app = ApiRegistry.register_api("/core-api/")

        @default_app.get("/ping")
        def ping() -> dict:
            return {"ok": True}

        @default_app.get("/boom")
        def default_boom() -> None:
            raise RuntimeError("default boom")

        public_app = ApiRegistry.register_api("/brick/pub/", cors=CorsPolicy(origins=["*"]))

        @public_app.get("/stats")
        def stats() -> dict:
            return {"n": 1}

        @public_app.get("/boom")
        def public_boom() -> None:
            raise RuntimeError("public boom")

        bare_app = ApiRegistry.register_api("/bare/", with_security_headers=False)

        @bare_app.get("/ping")
        def bare_ping() -> dict:
            return {"ok": True}

        @bare_app.get("/boom")
        def bare_boom() -> None:
            raise RuntimeError("bare boom")

        # Pin the lab policy to a fake cloud virtual host (bypass Settings)
        CorsConfig._get_allow_origin_regex = classmethod(  # type: ignore[method-assign]
            lambda _cls: r"https://.*\.mylab\.io"
        )

        for path, sub_app in ApiRegistry.get_all_apis().items():
            main_app.mount(path, sub_app)

        cls.client = TestClient(main_app, raise_server_exceptions=False)

    @classmethod
    def tearDownClass(cls) -> None:
        ApiRegistry._apis = cls._saved_apis
        ApiRegistry._silent_paths = cls._saved_silent_paths
        CorsConfig._get_allow_origin_regex = cls._saved_origin_regex  # type: ignore[method-assign]

    def test_default_app_preflight(self):
        # Lab origin: allowed, with credentials
        response = self.client.options(
            "/core-api/ping",
            headers={"Origin": LAB_ORIGIN, "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], LAB_ORIGIN)
        self.assertEqual(response.headers["access-control-allow-credentials"], "true")

        # Third-party origin: rejected
        response = self.client.options(
            "/core-api/ping",
            headers={"Origin": THIRD_PARTY_ORIGIN, "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_custom_app_preflight(self):
        # Third-party GET: allowed, credential-less
        response = self.client.options(
            "/brick/pub/stats",
            headers={"Origin": THIRD_PARTY_ORIGIN, "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "*")
        self.assertNotIn("access-control-allow-credentials", response.headers)

        # POST: rejected, the policy is GET-only
        response = self.client.options(
            "/brick/pub/stats",
            headers={"Origin": THIRD_PARTY_ORIGIN, "Access-Control-Request-Method": "POST"},
        )
        self.assertEqual(response.status_code, 400)

        # Lab origin on the custom app: the app policy applies, NOT the lab default
        # (no fallback) — so no credentials even for a lab origin
        response = self.client.options(
            "/brick/pub/stats",
            headers={"Origin": LAB_ORIGIN, "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("access-control-allow-credentials", response.headers)

    def test_simple_requests(self):
        response = self.client.get("/brick/pub/stats", headers={"Origin": THIRD_PARTY_ORIGIN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "*")

        response = self.client.get("/core-api/ping", headers={"Origin": LAB_ORIGIN})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], LAB_ORIGIN)

        response = self.client.get("/core-api/ping", headers={"Origin": THIRD_PARTY_ORIGIN})
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_server_error_responses(self):
        # A 500 is produced by the sub-app's ServerErrorMiddleware, ABOVE its CORS
        # middleware, so ExceptionHandler stamps the headers manually — and must
        # follow the policy of the app owning the path
        response = self.client.get("/brick/pub/boom", headers={"Origin": THIRD_PARTY_ORIGIN})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")

        response = self.client.get("/core-api/boom", headers={"Origin": LAB_ORIGIN})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers.get("access-control-allow-origin"), LAB_ORIGIN)

        response = self.client.get("/core-api/boom", headers={"Origin": THIRD_PARTY_ORIGIN})
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_security_headers(self):
        # Normal response
        response = self.client.get("/core-api/ping")
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertIn("content-security-policy", response.headers)

        # Preflight response: the security-headers middleware sits OUTSIDE the
        # CORS middleware, so even responses the CORS middleware answers itself
        # carry the headers
        response = self.client.options(
            "/core-api/ping",
            headers={"Origin": LAB_ORIGIN, "Access-Control-Request-Method": "GET"},
        )
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")

        # 500: bypasses the app's middleware, stamped by the generic exception handler
        response = self.client.get("/core-api/boom")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")

    def test_security_headers_disabled(self):
        # with_security_headers=False: no headers, on normal responses or 500s
        response = self.client.get("/bare/ping")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("x-content-type-options", response.headers)
        self.assertNotIn("content-security-policy", response.headers)

        response = self.client.get("/bare/boom")
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("x-content-type-options", response.headers)

    def test_handled_error_keeps_cors(self):
        # HTTPException responses (here a 404) come from ExceptionMiddleware, the
        # innermost layer, so they DO pass through the sub-app's CORS middleware
        response = self.client.get("/brick/pub/does-not-exist", headers={"Origin": THIRD_PARTY_ORIGIN})
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers.get("access-control-allow-origin"), "*")
