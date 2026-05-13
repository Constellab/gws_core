"""Code migration to gws_core 0.22.

Currently rewrites the deprecated ``allowed_values`` argument of
``StrParam`` / ``IntParam`` / ``FloatParam`` to the dedicated ``SelectParam``.
Add new 0.22 codemods to :meth:`Migration0220.get_codemods` as needed.
"""

from gws_cli.code_migration.code_migration import CodeMigration, Codemod, code_migration
from gws_cli.code_migration.codemods.allowed_values_to_select_param import (
    apply_to_source as allowed_values_to_select_param,
)


@code_migration(
    "0.22.0",
    short_description=(
        "Replace the deprecated `allowed_values` argument of StrParam/IntParam/FloatParam "
        "with the dedicated SelectParam: switch the class to SelectParam, rename "
        "`allowed_values=` to `options=`, and fix the related imports."
    ),
)
class Migration0220(CodeMigration):
    @classmethod
    def get_codemods(cls) -> list[Codemod]:
        return [allowed_values_to_select_param]
