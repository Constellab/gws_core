import hashlib
import json
import os
import re
import threading

from gws_core.apps.app_config import AppConfig
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class ReflexFrontBuildCache:
    """Shared cache of built Reflex frontends.

    Once a frontend build is instance-independent (same-origin backend URLs and no
    baked app id — see ReflexProcess build env), N instances of the same AppConfig app
    need only one `reflex export`: the first build fills the cache, later instances
    copy the built frontend into their own resource folder.

    Layout: `<brick-data>/<brick_name>/reflex-front-builds/<app typing name>/<key>`
    where `<key>` is `<brick_version>--<env hash>`. The brick version pins the app
    code; the env hash covers the values baked into the bundle that do not come from
    the code (external app port, backend path, cache format). A cache entry is filled
    atomically (staged, then renamed into place), so its existence means it is
    complete. Only AppConfig-based apps are cacheable: static-folder apps carry their
    code per resource.
    """

    CACHE_DIR_NAME = "reflex-front-builds"

    # bump when the build contract changes (e.g. new baked value) to invalidate all entries
    FORMAT_VERSION = 1

    _app_config: AppConfig
    _backend_path: str

    def __init__(self, app_config: AppConfig, backend_path: str):
        self._app_config = app_config
        self._backend_path = backend_path

    def get_app_cache_dir(self) -> str:
        """Cache directory of this app (holds one entry per brick version / env)."""
        settings = Settings.get_instance()
        app_name = re.sub(r"[^A-Za-z0-9_.-]", "_", self._app_config.get_typing_name())
        return os.path.join(
            settings.get_brick_data_dir(self._app_config.get_brick_name()),
            self.CACHE_DIR_NAME,
            app_name,
        )

    def get_entry_path(self) -> str:
        """Path of the cache entry for the current brick version and build env."""
        version = str(self._app_config.get_brick_version())
        return os.path.join(self.get_app_cache_dir(), f"{version}--{self._get_env_hash()}")

    def _get_env_hash(self) -> str:
        """Hash of the environment values baked into the bundle besides the app code."""
        env = {
            "format_version": self.FORMAT_VERSION,
            "external_port": Settings.get_app_external_port(),
            "backend_path": self._backend_path,
        }
        return hashlib.sha1(json.dumps(env, sort_keys=True).encode()).hexdigest()[:10]

    def get_cached_build_path(self) -> str | None:
        """Return the cached build folder if a complete entry exists, else None."""
        entry_path = self.get_entry_path()
        if os.path.isfile(os.path.join(entry_path, "index.html")):
            return entry_path
        return None

    def copy_into(self, destination_folder: str) -> None:
        """Copy the cached build content into a resource build folder."""
        cached_path = self.get_cached_build_path()
        if not cached_path:
            raise Exception(f"No cached build at {self.get_entry_path()}")
        FileHelper.create_dir_if_not_exist(destination_folder)
        FileHelper.copy_dir_content_to_dir(cached_path, destination_folder)

    def store_build(self, build_folder: str, instance_marker: str | None = None) -> bool:
        """Store a freshly built frontend in the cache.

        The build is staged (copied next to the final entry) then renamed into place,
        so a concurrent reader only ever sees a complete entry. If another builder
        stored the entry first, this build is discarded (all candidates are identical).

        :param build_folder: folder containing the built frontend (with index.html)
        :param instance_marker: value that must NOT appear in the bundle (typically the
            builder's resource id). If found, the bundle is instance-dependent (e.g. a
            user app reading instance env vars at module scope) and is not cached.
        :return: True if the entry is available in the cache after the call
        """
        entry_path = self.get_entry_path()
        if os.path.isdir(entry_path):
            return True

        if instance_marker and self._bundle_contains(build_folder, instance_marker):
            Logger.warning(
                f"Frontend build of app {self._app_config.get_typing_name()} contains the "
                f"instance id: the app bakes instance-specific values into the bundle, "
                "skipping the shared build cache for it."
            )
            return False

        app_cache_dir = self.get_app_cache_dir()
        FileHelper.create_dir_if_not_exist(app_cache_dir)
        staging_path = os.path.join(
            app_cache_dir, f".tmp-{os.getpid()}-{threading.get_ident()}"
        )
        FileHelper.delete_dir(staging_path)

        try:
            FileHelper.copy_dir(build_folder, staging_path)
            try:
                os.rename(staging_path, entry_path)
            except OSError:
                # another builder stored an (identical) entry first
                if not os.path.isdir(entry_path):
                    raise
        finally:
            FileHelper.delete_dir(staging_path)

        self._delete_stale_entries()
        return True

    def _delete_stale_entries(self) -> None:
        """Delete cache entries of other brick versions / envs for this app.

        The brick version is lab-wide, so older entries are unreachable.
        """
        app_cache_dir = self.get_app_cache_dir()
        current_name = os.path.basename(self.get_entry_path())
        try:
            for entry in os.listdir(app_cache_dir):
                if entry == current_name or entry.startswith(".tmp-"):
                    continue
                FileHelper.delete_dir(os.path.join(app_cache_dir, entry))
        except Exception as e:
            # GC only, never fail a build for it
            Logger.warning(
                f"Could not clean old cached builds of {self._app_config.get_typing_name()}: {e}"
            )

    def _bundle_contains(self, build_folder: str, marker: str) -> bool:
        """Check whether a text file of the bundle contains the marker string."""
        marker_bytes = marker.encode()
        for root, _dirs, files in os.walk(build_folder):
            for file_name in files:
                # compressed siblings mirror their plain file: checking the plain one is enough
                if file_name.endswith(".gz"):
                    continue
                try:
                    with open(os.path.join(root, file_name), "rb") as file:
                        if marker_bytes in file.read():
                            return True
                except OSError:
                    continue
        return False
