"""Generic one-shot download service for Reflex apps.

Large downloads served through the Reflex websocket event channel freeze the
UI while the payload is shipped. This service sidesteps that by streaming
files over a plain HTTP GET: callers write a file to disk, register it under
a single-use UUID token, and yield a small browser-side click event. A
FastAPI route mounted on the app's ``api_transformer`` pops the token and
returns a ``FileResponse``.

``rx.download(url=...)`` can't be used because it resolves URLs against the
*frontend* origin, but our FastAPI route is served by the *backend*. So
``trigger_download`` builds an absolute backend URL and injects a small
``<a>`` click via ``rx.call_script`` — mirroring what Reflex's internal
``_download`` handler does, but against the right origin.
"""

import json
import os
import threading
import uuid as _uuid
from dataclasses import dataclass
from urllib.parse import quote

import reflex as rx
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from gws_core.core.utils.settings import Settings


@dataclass
class _DownloadEntry:
    path: str
    filename: str
    media_type: str


class ReflexDownloadService:
    """Generic one-shot download service for Reflex apps.

    Typical usage:

    1. Mount the API once in your app entrypoint::

           from gws_reflex_main import ReflexDownloadService

           app = register_gws_reflex_app(rxe.App(...))
           app.api_transformer = ReflexDownloadService.build_api()

       Or, if your app already composes its own FastAPI sub-app, attach the
       download route to it::

           api = FastAPI()
           ReflexDownloadService.register_routes(api)
           app.api_transformer = api

    2. In a background event, write your file and register it::

           path = ReflexDownloadService.make_temp_path(suffix=".xlsx")
           df.to_excel(path)
           token = ReflexDownloadService.register(
               path,
               filename="results.xlsx",
               media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
           )
           yield ReflexDownloadService.trigger_download(token, "results.xlsx")

    Tokens are single-use: the first GET consumes the entry, subsequent
    requests 404. Files are NOT auto-deleted — callers decide lifetime. Use
    :meth:`make_temp_path` to place files under the lab's managed tmp dir so
    they share the lab's storage volume and cleanup policies instead of
    landing on ``/tmp``.
    """

    ROUTE_PREFIX: str = "/gws_reflex_download"

    _entries: dict[str, _DownloadEntry] = {}
    _lock: threading.Lock = threading.Lock()

    @classmethod
    def register(cls, path: str, filename: str, media_type: str) -> str:
        """Register a file for one-shot download and return the token.

        :param path: Absolute path to the file on disk (must exist when the
            download is requested).
        :param filename: Name presented to the browser (sets the
            ``Content-Disposition`` filename).
        :param media_type: MIME type for the ``Content-Type`` header.
        :return: Single-use UUID token to pass to :meth:`trigger_download`.
        """
        token = _uuid.uuid4().hex
        with cls._lock:
            cls._entries[token] = _DownloadEntry(
                path=path, filename=filename, media_type=media_type
            )
        return token

    @classmethod
    def make_temp_path(cls, suffix: str = "") -> str:
        """Return a unique filesystem path under the lab's managed tmp dir.

        Delegates to :meth:`Settings.make_temp_dir` for the directory, then
        joins ``download{suffix}`` onto it. Each call gets its own fresh
        directory so concurrent downloads can't collide on filenames.

        :param suffix: Optional file extension, e.g. ``".xlsx"``.
        :return: Absolute path the caller should write to.
        """
        tmp_dir = Settings.make_temp_dir()
        return os.path.join(tmp_dir, f"download{suffix}")

    @classmethod
    def build_api(cls) -> FastAPI:
        """Return a FastAPI sub-app exposing the download route.

        Intended to be assigned to ``app.api_transformer`` on a Reflex app.
        """
        api = FastAPI()
        cls.register_routes(api)
        return api

    @classmethod
    def register_routes(cls, api: FastAPI) -> None:
        """Attach the download route to an existing FastAPI sub-app.

        Use this when your app already composes its own FastAPI sub-app and
        you want to add the generic download route alongside your own.
        """

        @api.get(f"{cls.ROUTE_PREFIX}/{{token}}")
        def download_token(token: str) -> FileResponse:
            entry = cls._pop(token)
            print(f"Download requested: {token} -> {entry.path if entry else 'NOT FOUND'}")
            if entry is None or not os.path.isfile(entry.path):
                raise HTTPException(status_code=404, detail="Download expired or not found")
            return FileResponse(
                path=entry.path,
                media_type=entry.media_type,
                filename=entry.filename,
            )

    @classmethod
    def trigger_download(cls, token: str, filename: str) -> rx.event.EventSpec:
        """Reflex event that triggers the browser download via the backend URL.

        ``rx.download`` resolves URLs against the frontend origin, which
        doesn't serve our FastAPI route. We inject a scripted ``<a>`` click
        against an absolute backend URL instead.
        """
        url = cls._backend_download_url(token)
        js = (
            "(() => {"
            "const a = document.createElement('a');"
            f"a.href = {json.dumps(url)};"
            f"a.download = {json.dumps(filename)};"
            "a.hidden = true;"
            "document.body.appendChild(a);"
            "a.click();"
            "a.remove();"
            "})()"
        )
        return rx.call_script(js)

    @classmethod
    def _pop(cls, token: str) -> _DownloadEntry | None:
        with cls._lock:
            return cls._entries.pop(token, None)

    @classmethod
    def _backend_download_url(cls, token: str) -> str:
        # Read lazily so launchers that set the var after import still work.
        # GWS_REFLEX_API_URL is set by gws_core's reflex_process launcher.
        backend_url = (os.environ.get("GWS_REFLEX_API_URL") or "").rstrip("/")
        return f"{backend_url}{cls.ROUTE_PREFIX}/{quote(token)}"
