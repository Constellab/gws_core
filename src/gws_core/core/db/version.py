

class Version():
    """Object that represent a version like : 1.2.0

    :raises VersionInvalidException: [description]
    :raises VersionInvalidException: [description]
    :raises VersionInvalidException: [description]
    """

    major: int
    minor: int
    patch: int

    def __init__(self, version: str):
        self._init_from_str(version)

    def _init_from_str(self, version: str) -> None:
        """Mehod to checkthe version str and set attributes
        """
        try:
            parts = version.split('.')

            if len(parts) != 3:
                raise VersionInvalidException(version)

            major = int(parts[0])
            minor = int(parts[1])
            patch = int(parts[2])

            if major < 0 or minor < 0 or patch < 0:
                raise VersionInvalidException(version)

            self.major = major
            self.minor = minor
            self.patch = patch

        except:
            raise VersionInvalidException(version)

    def get_version_as_int(self) -> int:
        """return 1 int that is a concat of version number, this is useful for comparing/sorting versions
        """
        return int(str(self.major) + str(self.minor) + str(self.patch))

    def __eq__(self, other) -> bool:
        if other is None or not isinstance(other, Version):
            return False
        return self.get_version_as_int() == other.get_version_as_int()

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other:  'Version'):
        return self.get_version_as_int() < other.get_version_as_int()

    def __le__(self, other:  'Version'):
        return self.get_version_as_int() <= other.get_version_as_int()

    def __gt__(self, other:  'Version'):
        return self.get_version_as_int() > other.get_version_as_int()

    def __ge__(self, other:  'Version'):
        return self.get_version_as_int() >= other.get_version_as_int()

    def __str__(self) -> str:
        return str(self.major) + '.' + str(self.minor) + '.' + str(self.patch)


class VersionInvalidException(Exception):
    def __init__(self, str_version: str) -> None:
        super().__init__(f"Version '{str_version}' invalid. Must be formatted like '1.2.0'")
