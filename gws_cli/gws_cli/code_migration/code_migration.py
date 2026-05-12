"""Versioned source-code migrations for bricks.

This is the source-code counterpart of the DB migration framework
(``gws_core.core.db.migration``): just like ``@brick_migration("0.21.0", ...)``
declares a database migration, ``@code_migration("0.22.0", ...)`` declares a
set of source-to-source refactors (codemods) that should be applied when a brick
is upgraded to that version of gws_core.

A *codemod* is any callable ``(source: str) -> (new_source: str, report: CodemodResult)``
where ``report`` exposes at least ``changed: bool``, ``converted_count: int`` and
``warnings: list[str]``. New migrations just register a class returning such
callables; the discovery / version-filtering / interactive-review logic lives in
:mod:`gws_cli.code_migration.code_migration_runner`.
"""

from __future__ import annotations

import importlib
import pkgutil
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Protocol

from gws_core.core.db.version import Version


class CodemodResult(Protocol):
    """Per-file outcome returned by a codemod."""

    changed: bool
    converted_count: int
    warnings: list[str]


Codemod = Callable[[str], "tuple[str, CodemodResult]"]


class CodeMigration(ABC):
    """Base class for a versioned set of codemods.

    Subclasses must be decorated with :func:`code_migration` and implement
    :meth:`get_codemods`.
    """

    # set by the @code_migration decorator
    version: Version
    short_description: str

    @classmethod
    @abstractmethod
    def get_codemods(cls) -> list[Codemod]:
        """Return the ordered list of codemods that make up this migration.

        Each codemod is applied to every python file of the brick (see the runner).
        """


# ---------------------------------------------------------------------------- #
# Registry
# ---------------------------------------------------------------------------- #

# version string -> CodeMigration subclass
_REGISTRY: dict[str, type[CodeMigration]] = {}


def code_migration(version: str, short_description: str) -> Callable[[type[CodeMigration]], type[CodeMigration]]:
    """Decorator registering a :class:`CodeMigration` subclass under ``version``.

    :param version: the gws_core version this migration belongs to (e.g. ``"0.22.0"``).
    :param short_description: one-line summary shown by ``gws brick code-migrate --list``.
    """

    def decorator(cls: type[CodeMigration]) -> type[CodeMigration]:
        if not (isinstance(cls, type) and issubclass(cls, CodeMigration)):
            raise TypeError("@code_migration can only decorate a CodeMigration subclass")
        if version in _REGISTRY:
            raise ValueError(f"A code migration is already registered for version '{version}'")
        cls.version = Version(version)
        cls.short_description = short_description
        _REGISTRY[version] = cls
        return cls

    return decorator


def _ensure_migrations_imported() -> None:
    """Import every module in the ``migrations`` package so each ``@code_migration`` runs."""
    # imported lazily to avoid a circular import at module load time
    from gws_cli.code_migration import migrations

    for module_info in pkgutil.iter_modules(migrations.__path__, migrations.__name__ + "."):
        importlib.import_module(module_info.name)


def get_all_code_migrations() -> list[type[CodeMigration]]:
    """Return every registered code migration, sorted by version (ascending)."""
    _ensure_migrations_imported()
    return sorted(_REGISTRY.values(), key=lambda m: m.version)


def get_code_migration(version: str) -> type[CodeMigration] | None:
    """Return the code migration registered for ``version``, or ``None``."""
    _ensure_migrations_imported()
    return _REGISTRY.get(version)


def get_code_migrations_after(version: Version) -> list[type[CodeMigration]]:
    """Return every code migration strictly newer than ``version`` (ascending)."""
    return [m for m in get_all_code_migrations() if m.version > version]
