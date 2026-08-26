"""libcst codemod that migrates the deprecated ``allowed_values`` argument of
``StrParam`` / ``IntParam`` / ``FloatParam`` to the dedicated ``SelectParam``.

Transformation rules:

- ``StrParam(..., allowed_values=X, ...)`` -> ``SelectParam(..., options=X, ...)``
  (same for ``IntParam`` / ``FloatParam``). Only calls that actually pass the
  ``allowed_values`` keyword are touched; that keyword is renamed to ``options``
  (the name of the equivalent argument on ``SelectParam``).
- A call that combines ``allowed_values`` with one of the numeric/length bounds
  (``min_value`` / ``max_value`` / ``min_length`` / ``max_length``) is left
  untouched and reported, since ``SelectParam`` does not support those bounds.
- Imports are fixed up afterwards:
  - the original param class is removed from its ``from ...param_spec import`` line
    if it is no longer referenced anywhere in the module;
  - ``from gws_core.config.param.select_param import SelectParam`` is added if it
    is now used and not already imported.

The codemod is idempotent: re-running it on already-migrated code is a no-op.
"""

from __future__ import annotations

import libcst as cst
import libcst.matchers as m

# Param classes whose `allowed_values` kwarg is deprecated in favour of SelectParam.
DEPRECATED_PARAM_CLASSES = ("StrParam", "IntParam", "FloatParam")

# Bound kwargs that SelectParam does not support; presence of any of these next to
# `allowed_values` means we cannot safely auto-convert the call.
INCOMPATIBLE_KWARGS = ("min_value", "max_value", "min_length", "max_length")

# the deprecated keyword on the old param classes -> its name on SelectParam
OLD_KWARG_NAME = "allowed_values"
NEW_KWARG_NAME = "options"

SELECT_PARAM_MODULE = "gws_core.config.param.select_param"
SELECT_PARAM_NAME = "SelectParam"


def _module_parts(node: cst.ImportFrom) -> list[str]:
    """Return the dotted module path of a ``from X import ...`` as a list of names."""
    parts: list[str] = []
    module = node.module
    while isinstance(module, cst.Attribute):
        parts.append(module.attr.value)
        module = module.value
    if isinstance(module, cst.Name):
        parts.append(module.value)
    parts.reverse()
    return parts


def _module_ends_with(node: cst.ImportFrom, last_part: str) -> bool:
    parts = _module_parts(node)
    return bool(parts) and parts[-1] == last_part


def _module_contains_part(node: cst.ImportFrom, part: str) -> bool:
    return part in _module_parts(node)


def _import_targets_param_spec(node: cst.ImportFrom) -> bool:
    return _module_ends_with(node, "param_spec")


def _import_targets_select_param(node: cst.ImportFrom) -> bool:
    return _module_ends_with(node, "select_param")


class _CallRewriter(cst.CSTTransformer):
    """First pass: rename deprecated param calls that use ``allowed_values``."""

    def __init__(self) -> None:
        super().__init__()
        self.converted_calls = 0
        self.skipped_calls: list[str] = []
        self.changed = False

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.BaseExpression:  # noqa: N802
        func = updated_node.func
        if not (isinstance(func, cst.Name) and func.value in DEPRECATED_PARAM_CLASSES):
            return updated_node

        kwargs = {arg.keyword.value for arg in updated_node.args if arg.keyword is not None}
        if OLD_KWARG_NAME not in kwargs:
            return updated_node

        incompatible = sorted(kwargs & set(INCOMPATIBLE_KWARGS))
        if incompatible:
            self.skipped_calls.append(
                f"{func.value}({OLD_KWARG_NAME}=..., {', '.join(incompatible)}=...) "
                f"- SelectParam does not support {', '.join(incompatible)}; left unchanged"
            )
            return updated_node

        # rename the `allowed_values=...` keyword argument to `options=...`
        new_args = [
            arg.with_changes(keyword=cst.Name(NEW_KWARG_NAME))
            if arg.keyword is not None and arg.keyword.value == OLD_KWARG_NAME
            else arg
            for arg in updated_node.args
        ]

        self.converted_calls += 1
        self.changed = True
        return updated_node.with_changes(func=cst.Name(SELECT_PARAM_NAME), args=new_args)


class _NameCollector(cst.CSTVisitor):
    """Collect the set of bare names referenced in the module, excluding names that
    only appear inside ``import`` / ``from ... import`` statements."""

    def __init__(self) -> None:
        super().__init__()
        self.used_names: set[str] = set()
        self._in_import = 0

    def visit_Import(self, node: cst.Import) -> None:  # noqa: N802
        self._in_import += 1

    def leave_Import(self, original_node: cst.Import) -> None:  # noqa: N802
        self._in_import -= 1

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:  # noqa: N802
        self._in_import += 1

    def leave_ImportFrom(self, original_node: cst.ImportFrom) -> None:  # noqa: N802
        self._in_import -= 1

    def visit_Name(self, node: cst.Name) -> None:  # noqa: N802
        if self._in_import == 0:
            self.used_names.add(node.value)


class _ImportFixer(cst.CSTTransformer):
    """Second pass: clean up the imports given the post-rewrite name usage."""

    def __init__(self, used_names: set[str]) -> None:
        super().__init__()
        self._used_names = used_names
        self._select_param_already_imported = False
        # captured from the param_spec import line we touch, so the new select_param
        # import matches its relative-import depth (e.g. `....config.param.select_param`)
        self._param_spec_relative_dots: tuple[cst.Dot, ...] | None = None

    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:  # noqa: N802
        if _import_targets_select_param(node) and not isinstance(node.names, cst.ImportStar):
            for alias in node.names:
                if m.matches(alias.name, m.Name(SELECT_PARAM_NAME)):
                    self._select_param_already_imported = True

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:  # noqa: N802
        new_body: list[cst.BaseStatement] = []
        # index (in new_body) right after the last `config.param.*` import line, or
        # where a fully-removed `param_spec` import used to be - that's where we put
        # the new `select_param` import so it stays grouped with its siblings.
        anchor_index = -1
        for stmt in updated_node.body:
            cleaned = self._clean_param_spec_import(stmt)
            if cleaned is None:
                # the whole param_spec import line was removed - take its slot
                anchor_index = len(new_body)
                continue
            if self._is_config_param_import(cleaned):
                anchor_index = len(new_body) + 1
            new_body.append(cleaned)

        if SELECT_PARAM_NAME in self._used_names and not self._select_param_already_imported:
            select_import = cst.SimpleStatementLine(body=[self._make_select_param_import()])
            insert_at = anchor_index if anchor_index >= 0 else self._first_import_index(new_body)
            new_body.insert(insert_at, select_import)

        return updated_node.with_changes(body=new_body)

    # --------------------------------------------------------------------- #
    # helpers
    # --------------------------------------------------------------------- #

    def _make_select_param_import(self) -> cst.ImportFrom:
        """Build the ``from <...>config.param.select_param import SelectParam`` node.

        Uses the relative-import depth captured from the param_spec import line if
        the file uses relative imports there; otherwise an absolute import.
        """
        alias = [cst.ImportAlias(name=cst.Name(SELECT_PARAM_NAME))]
        if self._param_spec_relative_dots:
            return cst.ImportFrom(
                relative=list(self._param_spec_relative_dots),
                module=self._dotted_module("config.param.select_param"),
                names=alias,
            )
        return cst.ImportFrom(module=self._dotted_module(SELECT_PARAM_MODULE), names=alias)

    @staticmethod
    def _dotted_module(dotted: str) -> cst.Attribute | cst.Name:
        parts = dotted.split(".")
        node: cst.Attribute | cst.Name = cst.Name(parts[0])
        for part in parts[1:]:
            node = cst.Attribute(value=node, attr=cst.Name(part))
        return node

    @staticmethod
    def _is_config_param_import(stmt: cst.BaseStatement) -> bool:
        """True for `from <...>config.param[.<x>] import ...` lines (any depth)."""
        if not isinstance(stmt, cst.SimpleStatementLine):
            return False
        for small in stmt.body:
            if not isinstance(small, cst.ImportFrom):
                continue
            if _module_contains_part(small, "param") and _module_contains_part(small, "config"):
                return True
            # also covers `from gws_core.config.param.select_param import ...`
            if _import_targets_select_param(small) or _import_targets_param_spec(small):
                return True
        return False

    @staticmethod
    def _first_import_index(body: list[cst.BaseStatement]) -> int:
        for i, stmt in enumerate(body):
            if isinstance(stmt, cst.SimpleStatementLine) and any(
                isinstance(small, (cst.Import, cst.ImportFrom)) for small in stmt.body
            ):
                return i
        return 0

    def _clean_param_spec_import(self, stmt: cst.BaseStatement) -> cst.BaseStatement | None:
        """Drop now-unused deprecated param classes from a ``from ...param_spec import`` line.

        Returns the (possibly modified) statement, or ``None`` if the whole line
        should be removed.
        """
        if not isinstance(stmt, cst.SimpleStatementLine):
            return stmt

        new_small_stmts: list[cst.BaseSmallStatement] = []
        for small in stmt.body:
            if isinstance(small, cst.ImportFrom) and _import_targets_param_spec(small):
                # remember the relative-import depth so the new select_param import
                # matches it (e.g. `from ....config.param.select_param import ...`)
                if small.relative and self._param_spec_relative_dots is None:
                    self._param_spec_relative_dots = tuple(small.relative)
                if isinstance(small.names, cst.ImportStar):
                    new_small_stmts.append(small)
                    continue
                kept = [
                    alias
                    for alias in small.names
                    if not (
                        m.matches(alias.name, m.Name())
                        and alias.name.value in DEPRECATED_PARAM_CLASSES
                        and alias.name.value not in self._used_names
                    )
                ]
                if not kept:
                    continue  # whole import line is now empty -> drop it
                kept = [a.with_changes(comma=cst.MaybeSentinel.DEFAULT) for a in kept]
                new_small_stmts.append(small.with_changes(names=kept))
            else:
                new_small_stmts.append(small)

        if not new_small_stmts:
            return None
        return stmt.with_changes(body=new_small_stmts)


class _Result:
    """Per-file outcome of this codemod (implements the CodemodResult protocol)."""

    def __init__(self, changed: bool, converted_count: int, warnings: list[str]) -> None:
        self.changed = changed
        self.converted_count = converted_count
        self.warnings = warnings


def apply_to_source(source: str) -> tuple[str, _Result]:
    """Run the codemod on a python source string.

    :param source: the original python source.
    :return: a tuple ``(new_source, result)``. ``new_source`` equals ``source``
             when nothing changed.
    """
    module = cst.parse_module(source)

    rewriter = _CallRewriter()
    module = module.visit(rewriter)

    if not rewriter.changed:
        return source, _Result(False, 0, rewriter.skipped_calls)

    collector = _NameCollector()
    module.visit(collector)

    module = module.visit(_ImportFixer(collector.used_names))

    return module.code, _Result(True, rewriter.converted_calls, rewriter.skipped_calls)
