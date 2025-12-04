import os
import shutil
from json import load

from gws_core.brick.brick_helper import BrickHelper
from gws_core.core.classes.file_downloader import FileDownloader
from gws_core.core.classes.observer.message_dispatcher import MessageDispatcher
from gws_core.core.classes.observer.message_observer import LoggerMessageObserver
from gws_core.core.utils.logger import Logger
from gws_core.core.utils.settings import Settings
from gws_core.impl.file.file_helper import FileHelper


class AppPluginDownloader:
    """Class to download and manage dashboard component packages from GitHub releases.

    This class handles downloading component packages (iframe-message and streamlit-components)
    from a unified version release structure. The packages are stored in:
    dc_2.0.0/
        ├── iframe-message.zip
        └── streamlit-components.zip

    Features:
    - Downloads packages from GitHub releases
    - Manages versioning with version.json files
    - Automatically decompresses zip files
    - Caches downloaded packages to avoid redundant downloads
    - Supports local installation from a pre-unzipped folder when IS_RELEASE is True and in local environment
    """

    # If True and Settings.is_local_dev_env() is True, use local gws_plugin folder instead of downloading
    IS_RELEASE = True

    # Path to the local plugin folder (already unzipped) used when IS_RELEASE is True
    LOCAL_PLUGIN_PATH = "/lab/user/bricks/gws_core/.data/browser"

    VERSION_FILE_NAME = "version.json"
    VERSION_KEY = "version"

    RELEASE_BASE_URL = "https://github.com/Constellab/dashboard-components/releases/download/"

    # Main version that contains both packages
    DASHBOARD_COMPONENTS_VERSION = "dc_1.0.1"

    # Package names
    STREAMLIT_IFRAME_MESSAGE = "streamlit-iframe-message"
    STREAMLIT_COMPONENTS = "streamlit-components"
    REFLEX_COMPONENTS = "reflex-components"

    package_name: str
    message_dispatcher: MessageDispatcher
    destination_folder: str

    def __init__(self, package_name: str, destination_folder: str = None, message_dispatcher: MessageDispatcher = None):
        """Initialize the ComponentPackageDownloader.

        :param package_name: Name of the package to manage (iframe-message or streamlit-components)
        :type package_name: str
        :param destination_folder: Optional custom destination folder for packages. If None, uses the default brick data directory, defaults to None
        :type destination_folder: str, optional
        :param message_dispatcher: Optional message dispatcher for logging, defaults to None
        :type message_dispatcher: MessageDispatcher, optional
        """
        available_packages = [self.STREAMLIT_IFRAME_MESSAGE, self.STREAMLIT_COMPONENTS, self.REFLEX_COMPONENTS]
        if package_name not in available_packages:
            raise ValueError(f"Invalid package name: {package_name}. Must be either {', '.join(available_packages)}.")

        if message_dispatcher is None:
            message_dispatcher = MessageDispatcher()
            message_dispatcher.attach(LoggerMessageObserver())

        self.package_name = package_name
        self.message_dispatcher = message_dispatcher

        if destination_folder:
            self.destination_folder = destination_folder
        else:
            settings = Settings.get_instance()
            self.destination_folder = os.path.join(settings.get_brick_data_dir(BrickHelper.GWS_CORE), package_name)

    def get_version_folder_path(self) -> str:
        """Get the path to the version folder (e.g., dc_2.0.0).

        :return: Full path to the version folder
        :rtype: str
        """
        return os.path.join(self.destination_folder, self.DASHBOARD_COMPONENTS_VERSION)

    def install_package(self, force_download: bool = False) -> str:
        """Download and install a component package if needed.

        This method:
        1. Checks if the package is already downloaded with the correct version
        2. If not, calls post_install() which can be overridden by subclasses
        3. Returns the path to the installed package

        :param force_download: If True, force download even if package exists, defaults to False
        :type force_download: bool, optional
        :return: Path to the extracted package folder
        :rtype: str
        :raises Exception: If download or extraction fails
        """

        if self.is_development_mode():
            self._install_from_local_folder()
            return self.destination_folder

        # Check if package already exists with correct version
        if not force_download:
            existing_version = self.get_installed_version()
            if existing_version == self.DASHBOARD_COMPONENTS_VERSION:
                Logger.debug(f"Package {self.package_name} version {existing_version} is already installed.")
                return self.destination_folder

        # Uninstall existing package if it exists
        self.uninstall_package()

        # Download and install the package (calls post_install which can be overridden by subclasses)
        self._download_from_github()

        return self.destination_folder

    def _download_from_github(self) -> None:
        """Download and install the package from GitHub releases.
        This is the standard installation method.
        """

        # Ensure download destination exists
        parent_dir = os.path.dirname(self.destination_folder)
        folder_name = os.path.basename(self.destination_folder)
        FileHelper.create_dir_if_not_exist(parent_dir)

        # Download and extract the package
        Logger.info(f"Downloading package {self.package_name} version {self.DASHBOARD_COMPONENTS_VERSION}")

        file_downloader = FileDownloader(parent_dir, message_dispatcher=self.message_dispatcher)
        download_url = self._get_package_download_url(self.package_name)

        # Use custom folder name if provided, otherwise use package_name
        file_downloader.download_file_if_missing(download_url, folder_name, decompress_file=True)

        try:
            # Call post-install hook (can be overridden by subclasses)
            self.post_install()
        except Exception as e:
            Logger.error(f"Post-installation failed for package {self.package_name}: {e}")
            self.uninstall_package()
            raise e

        # Check if the package was downloaded successfully with the correct version
        installed_version = self.get_installed_version()
        if installed_version != self.DASHBOARD_COMPONENTS_VERSION:
            self.uninstall_package()
            raise Exception(
                f"Failed to download the package '{self.package_name}' version '{self.DASHBOARD_COMPONENTS_VERSION}'. "
                f"Installed version is '{installed_version}'."
            )

        Logger.info(f"Successfully installed package {self.package_name} version {self.DASHBOARD_COMPONENTS_VERSION}")

    def _install_from_local_folder(self) -> None:
        """Move the gws_plugin from the local folder to the destination.
        This is used when IS_RELEASE is True and Settings.is_local_dev_env() is True.

        The local folder should already contain the unzipped plugin files.
        If the source folder doesn't exist, this method does nothing (no error is raised).
        Version checking is skipped in this mode.
        """
        Logger.info(f"Installing package {self.package_name} from local folder: {self.LOCAL_PLUGIN_PATH}")
        if not os.path.exists(self.LOCAL_PLUGIN_PATH):
            Logger.info(
                f"Local plugin path does not exist: {self.LOCAL_PLUGIN_PATH}. Skipping installation from local folder."
            )
            return

        # Uninstall existing package if it exists
        self.uninstall_package()

        # Ensure destination parent directory exists
        parent_dir = os.path.dirname(self.destination_folder)
        FileHelper.create_dir_if_not_exist(parent_dir)

        # Remove existing destination folder if it exists
        if os.path.exists(self.destination_folder):
            FileHelper.delete_dir(self.destination_folder)

        # Move the entire local plugin folder to the destination
        shutil.move(self.LOCAL_PLUGIN_PATH, self.destination_folder)

        try:
            # Call post-install hook (can be overridden by subclasses)
            self.post_install()
        except Exception as e:
            Logger.error(f"Post-installation failed for package {self.package_name}: {e}")
            self.uninstall_package()
            raise e

        Logger.info(f"Successfully installed package {self.package_name} from local folder")

    def post_install(self) -> None:
        """Post-installation hook. Override this method in subclasses to add custom installation logic.
        By default, this method does nothing.
        """
        pass

    def uninstall_package(self) -> None:
        """Uninstall the package. This method can be overridden by subclasses to add custom cleanup logic.
        By default, it only deletes the package folder.
        """

        if FileHelper.exists_on_os(self.destination_folder):
            FileHelper.delete_dir(self.destination_folder)

        self.post_uninstall()

    def post_uninstall(self) -> None:
        """Post-uninstallation hook. Override this method in subclasses to add custom cleanup logic.
        By default, this method does nothing.
        """
        pass

    def get_installed_version(self) -> str | None:
        """Get the currently installed version of the package.

        :return: Version string if installed, None otherwise
        :rtype: str | None
        """
        return self._get_version_from_json()

    def is_package_installed(self) -> bool:
        """Check if the package is installed with the correct version.

        :return: True if package is installed with correct version, False otherwise
        :rtype: bool
        """
        installed_version = self.get_installed_version()
        return installed_version == self.DASHBOARD_COMPONENTS_VERSION

    def _get_version_from_json(self) -> str | None:
        """Read the version from a package's version.json file.

        :return: Version string if found, None otherwise
        :rtype: str | None
        """
        try:
            if FileHelper.exists_on_os(self.destination_folder):
                version_file_path = os.path.join(self.destination_folder, self.VERSION_FILE_NAME)
                if FileHelper.exists_on_os(version_file_path):
                    with open(version_file_path, encoding="UTF-8") as file:
                        version_json = load(file)
                        return version_json.get(self.VERSION_KEY)
        except Exception as e:
            Logger.error(f"Error reading version file at {self.destination_folder}: {e}")
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
