import fcntl
import json
import os
import shutil
import time
from collections.abc import Iterator
from contextlib import contextmanager
from json import load

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import LoggerMessageObserver
from gws_core.core.utils.compress.zip_compress import ZipCompress
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class AppPluginDownloader:
    """Class to download and manage dashboard component packages from GitHub releases.

    Packages are installed into a lab-wide, version-keyed store:
        <brick-data>/gws_core/<package_name>/<DASHBOARD_COMPONENTS_VERSION>/

    Because the version is part of the path, a store directory is immutable once
    complete: it is filled atomically (extracted into a temp dir, then renamed into
    place), so its mere existence means the content is complete. A new plugin version
    is a new directory. This makes concurrent installs from multiple processes safe:
    the filling is guarded by an `fcntl.flock` to avoid duplicate downloads, and even
    without the lock the atomic rename guarantees a complete tree.

    Optionally, the package can be *materialized* (plain copy) into a mutable target
    folder (e.g. a Reflex app's `assets/external/gws_plugin`, or the streamlit package
    static folder). Materialization is idempotent (skipped when the target already has
    the right version) and staged (copied to a temp sibling, then renamed into place).

    Features:
    - Downloads packages from GitHub releases
    - Manages versioning with version.json files
    - Concurrency-safe: atomic store fill + file lock across processes
    - Supports local installation from a pre-unzipped folder when IS_RELEASE is False
      and in local environment
    """

    # If False and Settings.is_local_dev_env() is True, use local gws_plugin folder instead of downloading
    IS_RELEASE = True

    # Path to the local plugin folder (already unzipped) used when IS_RELEASE is False
    LOCAL_PLUGIN_PATH = os.path.join(Settings.get_user_bricks_folder(), ".data", "browser")

    VERSION_FILE_NAME = "version.json"
    VERSION_KEY = "version"

    # Shared plugin file layout
    ASSETS_FOLDER_NAME = "assets"
    INDEX_HTML_FILE_NAME = "index.html"
    ENVIRONMENT_JSON_FILE_NAME = "environment.json"

    RELEASE_BASE_URL = "https://github.com/Constellab/dashboard-components/releases/download/"

    # Main version that contains both packages
    DASHBOARD_COMPONENTS_VERSION = "dc_1.0.12"

    # Package names
    STREAMLIT_IFRAME_MESSAGE = "streamlit-iframe-message"
    STREAMLIT_COMPONENTS = "streamlit-components"
    REFLEX_COMPONENTS = "reflex-components"

    # Folder name used by the dev-mode local install inside the store root
    _LOCAL_DEV_FOLDER_NAME = "local-dev"

    # number of attempts when swapping the materialized folder into place (the target
    # may be deleted concurrently, e.g. by a Reflex app cache clear)
    _MATERIALIZE_ATTEMPTS = 3

    package_name: str
    message_dispatcher: MessageDispatcher
    materialize_target: str | None

    def __init__(
        self,
        package_name: str,
        materialize_target: str | None = None,
        message_dispatcher: MessageDispatcher | None = None,
    ):
        """Initialize the AppPluginDownloader.

        :param package_name: Name of the package to manage
        :type package_name: str
        :param materialize_target: Optional folder where the package content is copied after
            the store install. If None, the package is only installed in the shared store
            and `install_package` returns the store path, defaults to None
        :type materialize_target: str, optional
        :param message_dispatcher: Optional message dispatcher for logging, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        available_packages = [
            self.STREAMLIT_IFRAME_MESSAGE,
            self.STREAMLIT_COMPONENTS,
            self.REFLEX_COMPONENTS,
        ]
        if package_name not in available_packages:
            raise ValueError(
                f"Invalid package name: {package_name}. Must be either {', '.join(available_packages)}."
            )

        if message_dispatcher is None:
            message_dispatcher = MessageDispatcher()
            message_dispatcher.attach(LoggerMessageObserver())

        self.package_name = package_name
        self.message_dispatcher = message_dispatcher
        self.materialize_target = materialize_target

    def get_store_root(self) -> str:
        """Root of the lab-wide store for this package (contains one folder per version)."""
        settings = Settings.get_instance()
        return os.path.join(settings.get_brick_data_dir(BrickHelper.GWS_CORE), self.package_name)

    def get_version_folder_path(self) -> str:
        """Path of the immutable store folder for the current version.

        :return: Full path to the version folder
        :rtype: str
        """
        return os.path.join(self.get_store_root(), self.DASHBOARD_COMPONENTS_VERSION)

    def get_install_path(self) -> str:
        """Path where the package content is available after `install_package`:
        the materialize target if one is set, otherwise the immutable store folder.
        """
        if self.materialize_target:
            return self.materialize_target
        if self.is_development_mode():
            return os.path.join(self.get_store_root(), self._LOCAL_DEV_FOLDER_NAME)
        return self.get_version_folder_path()

    def install_package(self, force_download: bool = False) -> str:
        """Install the package if needed and return the path to its content.

        This method:
        1. Returns immediately if the right version is already available at the install path
        2. Otherwise fills the shared store atomically (single download across concurrent
           callers thanks to a cross-process file lock)
        3. Materializes the content into the target folder when one is configured

        :param force_download: If True, force download even if package exists, defaults to False
        :type force_download: bool, optional
        :return: Path to the installed package folder
        :rtype: str
        :raises Exception: If download or extraction fails
        """

        if self.is_development_mode():
            self._install_from_local_folder()
            return self.get_install_path()

        # Fast path without lock: correct because the store fill and the materialization
        # are both atomic, so a matching version at the install path is always complete.
        if not force_download and self.is_package_installed():
            Logger.debug(
                f"Package {self.package_name} version {self.DASHBOARD_COMPONENTS_VERSION} "
                "is already installed."
            )
            if self.materialize_target:
                # the environment file depends on lab settings that can change without
                # a version bump: keep it fresh even when the install is skipped
                self._refresh_environment_file(self.materialize_target)
            return self.get_install_path()

        FileHelper.create_dir_if_not_exist(self.get_store_root())

        with self._version_file_lock():
            if force_download:
                FileHelper.delete_dir(self.get_version_folder_path())
                self.uninstall_package()

            # Re-check under the lock: another process may have finished the install
            # while this one was waiting for the lock.
            if not self.is_package_installed():
                self._ensure_store_version()
                self._materialize()

        return self.get_install_path()

    @contextmanager
    def _version_file_lock(self) -> Iterator[None]:
        """Cross-process lock scoped to (package, version).

        Only an optimization to avoid duplicate downloads/copies: correctness does not
        depend on it (the store fill and the materialization are atomic renames).
        """
        lock_path = os.path.join(
            self.get_store_root(), f"{self.DASHBOARD_COMPONENTS_VERSION}.lock"
        )
        with open(lock_path, "w", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)

    def _ensure_store_version(self) -> None:
        """Fill the store version folder if it does not exist yet.

        The zip is downloaded to a temp dir, extracted into a temp sibling of the final
        folder (same filesystem), verified, then renamed into place. The rename is atomic,
        so the version folder either does not exist or is complete — a partially extracted
        tree can never be mistaken for an installed package.
        """
        version_folder = self.get_version_folder_path()
        if os.path.isdir(version_folder):
            return

        Logger.info(
            f"Downloading package {self.package_name} version {self.DASHBOARD_COMPONENTS_VERSION}"
        )

        staging_folder = os.path.join(
            self.get_store_root(), f".tmp-{self.DASHBOARD_COMPONENTS_VERSION}-{os.getpid()}"
        )
        FileHelper.delete_dir(staging_folder)
        download_folder = Settings.make_temp_dir()

        try:
            file_downloader = FileDownloader(
                download_folder, message_dispatcher=self.message_dispatcher
            )
            zip_path = file_downloader.download_file(
                url=self._get_package_download_url(self.package_name),
                filename=f"{self.package_name}.zip",
            )
            ZipCompress.decompress(zip_path, staging_folder)

            extracted_version = self._get_version_from_json(staging_folder)
            if extracted_version != self.DASHBOARD_COMPONENTS_VERSION:
                raise Exception(
                    f"Failed to download the package '{self.package_name}' version "
                    f"'{self.DASHBOARD_COMPONENTS_VERSION}'. Downloaded version is "
                    f"'{extracted_version}'."
                )

            try:
                os.rename(staging_folder, version_folder)
            except OSError:
                # Another process renamed its own (identical) staging folder first.
                if not os.path.isdir(version_folder):
                    raise

            self._delete_stale_store_versions()

            Logger.info(
                f"Successfully installed package {self.package_name} "
                f"version {self.DASHBOARD_COMPONENTS_VERSION}"
            )
        finally:
            FileHelper.delete_dir(staging_folder)
            FileHelper.delete_dir(download_folder)

    def _delete_stale_store_versions(self) -> None:
        """Delete store folders and lock files of other (older) versions of this package."""
        store_root = self.get_store_root()
        current_names = {
            self.DASHBOARD_COMPONENTS_VERSION,
            f"{self.DASHBOARD_COMPONENTS_VERSION}.lock",
            self._LOCAL_DEV_FOLDER_NAME,
        }
        try:
            for entry in os.listdir(store_root):
                if entry in current_names or entry.startswith(".tmp-"):
                    continue
                path = os.path.join(store_root, entry)
                if os.path.isdir(path):
                    FileHelper.delete_dir(path)
                else:
                    FileHelper.delete_file(path)
        except Exception as e:
            # GC only, never fail an install for it
            Logger.warning(f"Could not clean old versions of package {self.package_name}: {e}")

    def _materialize(self) -> None:
        """Copy the store content into the materialize target (if configured).

        Skipped when the target already holds the right version (the environment file is
        still refreshed, as it depends on lab settings that can change without a version
        bump). The copy is staged next to the target and renamed into place, with a few
        retries because the target's parent can be deleted concurrently (e.g. a Reflex
        app cache clear from another app instance).
        """
        if not self.materialize_target:
            return

        target = self.materialize_target

        if self._target_is_up_to_date():
            self._refresh_environment_file(target)
            return

        version_folder = self.get_version_folder_path()

        last_error: Exception | None = None
        for _ in range(self._MATERIALIZE_ATTEMPTS):
            staging_folder = f"{target}.tmp-{os.getpid()}"
            try:
                FileHelper.delete_dir(staging_folder)
                FileHelper.create_dir_if_not_exist(os.path.dirname(target))
                shutil.copytree(version_folder, staging_folder)
                self.pre_materialize_finalize(staging_folder)

                if os.path.isdir(target):
                    FileHelper.delete_dir(target)
                os.rename(staging_folder, target)

                self.post_materialize()
                return
            except OSError as e:
                last_error = e
                FileHelper.delete_dir(staging_folder)
                # a concurrent materialization may have won the race
                if self._target_is_up_to_date():
                    return
                time.sleep(0.2)

        raise Exception(
            f"Failed to materialize package {self.package_name} into {target}: {last_error}"
        )

    def _target_is_up_to_date(self) -> bool:
        """True if the materialize target already holds the current version."""
        if not self.materialize_target:
            return False
        return (
            self._get_version_from_json(self.materialize_target)
            == self.DASHBOARD_COMPONENTS_VERSION
        )

    def _refresh_environment_file(self, target_folder: str) -> None:
        """Rewrite environment.json in an up-to-date target if this plugin uses one.

        The environment file is derived from lab settings (URLs) that can change without
        a plugin version bump, so it is refreshed even when the copy itself is skipped.
        """
        env_file = os.path.join(
            target_folder, self.ASSETS_FOLDER_NAME, self.ENVIRONMENT_JSON_FILE_NAME
        )
        if os.path.exists(env_file):
            self.create_environment_json_file(target_folder)

    def pre_materialize_finalize(self, staging_folder: str) -> None:
        """Hook called on the staging copy just before it is renamed into the target.
        Override in subclasses to add files (e.g. environment.json) so the target is
        complete the instant it appears. By default, does nothing.
        """

    def post_materialize(self) -> None:
        """Hook called after the target folder is in place. Override in subclasses for
        side effects outside the target folder (e.g. patching a host index.html).
        By default, does nothing.
        """

    def _install_from_local_folder(self) -> None:
        """Copy the gws_plugin from the local folder to the install path.
        This is used when IS_RELEASE is False and Settings.is_local_dev_env() is True.

        The local folder should already contain the unzipped plugin files, and is copied
        (not moved) so several apps can install from the same local build.
        If the source folder doesn't exist, this method does nothing (no error is raised).
        Version checking is skipped in this mode.
        """
        Logger.info(
            f"Installing package {self.package_name} from local folder: {self.LOCAL_PLUGIN_PATH}"
        )
        if not os.path.exists(self.LOCAL_PLUGIN_PATH):
            Logger.info(
                f"Local plugin path does not exist: {self.LOCAL_PLUGIN_PATH}. Skipping installation from local folder."
            )
            return

        # Uninstall existing package if it exists
        self.uninstall_package()

        install_path = self.get_install_path()
        FileHelper.create_dir_if_not_exist(os.path.dirname(install_path))
        shutil.copytree(self.LOCAL_PLUGIN_PATH, install_path)

        try:
            self.pre_materialize_finalize(install_path)
            self.post_materialize()
        except Exception as e:
            Logger.error(f"Post-installation failed for package {self.package_name}: {e}")
            self.uninstall_package()
            raise e

        Logger.info(f"Successfully installed package {self.package_name} from local folder")

    def get_base_href(self) -> str:
        """Relative path at which the plugin assets are served by the host app.
        Written to environment.json so the frontend can resolve asset URLs.
        Subclasses must override.
        """
        raise NotImplementedError(f"{type(self).__name__} must override get_base_href()")

    def get_plugin_assets_folder_path(self) -> str:
        """Path to the plugin's inner assets folder (<install path>/assets)."""
        return os.path.join(self.get_install_path(), self.ASSETS_FOLDER_NAME)

    def get_plugin_index_html_path(self) -> str:
        """Path to the plugin's index.html file."""
        return os.path.join(self.get_install_path(), self.INDEX_HTML_FILE_NAME)

    def create_environment_json_file(self, target_folder: str | None = None) -> None:
        """Create the environment.json file in the plugin's assets folder.
        The file contains lab-specific URLs resolved from Settings so the
        frontend plugin can call back into this lab.

        :param target_folder: plugin folder to write into; defaults to the install path
        :type target_folder: str, optional
        """
        dict_ = {
            "apiBaseUrl": Settings.get_lab_api_url(),
            "baseHref": self.get_base_href(),
            "spaceApiUrl": Settings.get_space_api_url(),
            "communityFrontUrl": Settings.get_community_front_url(),
            "communityApiUrl": Settings.get_community_api_url(),
        }

        if target_folder is None:
            target_folder = self.get_install_path()
        json_dir = os.path.join(target_folder, self.ASSETS_FOLDER_NAME)
        if not os.path.exists(json_dir):
            raise FileNotFoundError(f"The folder for json env {json_dir} does not exist.")

        json_file_path = os.path.join(json_dir, self.ENVIRONMENT_JSON_FILE_NAME)
        # write to a temp file then rename so a concurrent reader never sees a partial file
        tmp_file_path = f"{json_file_path}.tmp-{os.getpid()}"
        with open(tmp_file_path, "w", encoding="utf-8") as json_file:
            json.dump(dict_, json_file, indent=4)
        os.replace(tmp_file_path, json_file_path)

    def uninstall_package(self) -> None:
        """Uninstall the package from its install path (the materialize target when set).
        This method can be overridden by subclasses to add custom cleanup logic.
        """

        install_path = self.get_install_path()
        if FileHelper.exists_on_os(install_path):
            FileHelper.delete_dir(install_path)

        self.post_uninstall()

    def post_uninstall(self) -> None:
        """Post-uninstallation hook. Override this method in subclasses to add custom cleanup logic.
        By default, this method does nothing.
        """

    def get_installed_version(self) -> str | None:
        """Get the currently installed version of the package at the install path.

        :return: Version string if installed, None otherwise
        :rtype: str | None
        """
        return self._get_version_from_json(self.get_install_path())

    def is_package_installed(self) -> bool:
        """Check if the package is installed with the correct version.

        :return: True if package is installed with correct version, False otherwise
        :rtype: bool
        """
        installed_version = self.get_installed_version()
        return installed_version == self.DASHBOARD_COMPONENTS_VERSION

    def _get_version_from_json(self, folder_path: str) -> str | None:
        """Read the version from a package folder's version.json file.

        :param folder_path: folder that should contain the version.json file
        :type folder_path: str
        :return: Version string if found, None otherwise
        :rtype: str | None
        """
        try:
            if FileHelper.exists_on_os(folder_path):
                version_file_path = os.path.join(folder_path, self.VERSION_FILE_NAME)
                if FileHelper.exists_on_os(version_file_path):
                    with open(version_file_path, encoding="UTF-8") as file:
                        version_json = load(file)
                        return version_json.get(self.VERSION_KEY)
        except Exception as e:
            Logger.error(f"Error reading version file at {folder_path}: {e}")
        return None

    def _get_package_download_url(self, package_name: str) -> str:
        """Construct the download URL for a package.

        :param package_name: Name of the package
        :type package_name: str
        :return: Full download URL
        :rtype: str
        """
        return f"{self.RELEASE_BASE_URL}{self.DASHBOARD_COMPONENTS_VERSION}/{package_name}.zip"

    def is_development_mode(self) -> bool:
        """Check if the downloader is in development mode.

        :return: True if in development mode, False otherwise
        :rtype: bool
        """
        return Settings.is_local_dev_env() and not self.IS_RELEASE
