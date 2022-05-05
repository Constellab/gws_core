

from math import isnan

from numpy import Infinity


class Version():
    """Object that represent a version like : 1.2.0

    :raises VersionInvalidException: [description]
    :raises VersionInvalidException: [description]
    :raises VersionInvalidException: [description]
    """

    major: int
    minor: int
    patch: int
    sub_patch: int

    def __init__(self, version: str):
        self._init_from_str(version)

    def _init_from_str(self, version: str) -> None:
        """Mehod to checkthe version str and set attributes
        """
        try:
            versions = version.split('.')

            if len(versions) != 3 and len(versions) != 4:
                raise VersionInvalidException(version)

            main_version_str = version
            sub_patch: int = None

            # if the version contains a subpatch
            if '-beta.' in version:
                [main_version_str, sub_patch_str] = version.split('-beta.')

                sub_patch = int(sub_patch_str)
                if isnan(sub_patch):
                    raise VersionInvalidException(version)

            # retrieve main version
            main_versions = main_version_str.split('.')
            major = int(main_versions[0])
            minor = int(main_versions[1])
            patch = int(main_versions[2])

            if isnan(major) or major < 0 or isnan(minor) or minor < 0 or isnan(patch) or patch < 0:
                raise VersionInvalidException(version)

            self.major = major
            self.minor = minor
            self.patch = patch
            self.sub_patch = sub_patch

        except:
            raise VersionInvalidException(version)

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, Version):
            return False

        return self._get_dif(other) == 0

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other:  'Version'):
        return self._get_dif(other) < 0

    def __le__(self, other:  'Version'):
        return self._get_dif(other) <= 0

    def __gt__(self, other:  'Version'):
        return self._get_dif(other) > 0

    def __ge__(self, other:  'Version'):
        return self._get_dif(other) >= 0

    def __str__(self) -> str:
        version_str = str(self.major) + '.' + str(self.minor) + '.' + str(self.patch)

        if self.has_sub_patch():
            version_str += '-beta.' + str(self.sub_patch)
        return version_str

    def _get_dif(self, other: 'Version') -> int:
        """return the difference between self and other version
        """
        if self.major == other.major and self.minor == other.minor and self.patch == other.patch and self.get_sub_patch_as_number() == other.get_sub_patch_as_number():
            return 0

        if self.major > other.major or (
                self.major == other.major and self.minor > other.minor) or (
                self.major == other.major and self.minor == other.minor and self.patch > other.patch) or (
                self.major == other.major and self.minor == other.minor and self.patch == other.
                patch and self.get_sub_patch_as_number() > other.get_sub_patch_as_number()):
            return 1
        else:
            return -1

    def has_sub_patch(self) -> bool:
        """return True if the version has a sub_patch
        """
        return self.sub_patch is not None

    def get_sub_patch_as_number(self) -> int:
        """return the sub_patch as a number.
        In there is no sub patch, return infinity so the beta version are always before real version
        """
        return Infinity if self.sub_patch is None else self.sub_patch


class VersionInvalidException(Exception):
    def __init__(self, str_version: str) -> None:
        super().__init__(f"Version '{str_version}' invalid. Must be formatted like '1.2.0'")
