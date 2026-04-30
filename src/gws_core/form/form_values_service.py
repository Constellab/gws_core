import copy
import uuid
from typing import Any, ClassVar

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.form.form_dto import FormChangeAction, FormChangeEntry


class FormValuesService:
    """Values-layer helper for the form save flow.

    Stateless and DB-free — every method takes a ConfigSpecs and a values
    dict and returns a new dict (or a list of FormChangeEntry rows).

    Four responsibilities:

    1. ``assign_item_ids``  — assign / preserve a stable ``__item_id`` on
       every dict inside a ParamSet value, so per-item edits and reorders
       can be tracked across saves (spec §7).
    2. ``strip_computed_keys`` — defensive input-side strip: clients must
       never write to ComputedParam keys; the evaluator owns those. Storage
       is the union; this strip is on the *incoming* dto.values only.
    3. ``validate_with_specs`` — run ParamSpec.validate on every leaf,
       passing ParamSet rows in with ``__item_id`` removed so the dict
       validator doesn't flag the unknown reserved key.
    4. ``diff_values`` — recursive diff producing one FormChangeEntry per
       leaf change, using the field-path shape from spec §7:
           top-level scalar:           ``mass``
           ParamSet item field:        ``samples[item_id=<uuid>].mass``
           whole item add/remove:      ``samples[item_id=<uuid>]``
       Reorder = REMOVED + ADDED for the same ``__item_id`` (no MOVED action).

    There is also a fifth helper, ``merge_computed``, which writes the
    outer-scope computed dict from ``ConfigSpecs.compute_values`` into the
    union dict that gets persisted. (Per-row ParamSet computed cells are
    populated in-place by ``compute_values`` itself, so they don't need
    explicit merging here.)
    """

    ITEM_ID_KEY: ClassVar[str] = "__item_id"

    # ------------------------------------------------------------------ #
    # __item_id reconciliation
    # ------------------------------------------------------------------ #

    @classmethod
    def assign_item_ids(
        cls,
        specs: ConfigSpecs,
        incoming: dict[str, Any],
        previous: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Return a deep-copied values dict with ``__item_id`` populated on
        every ParamSet item.

        - existing ``__item_id`` values are preserved (rows kept across saves
          retain their identity, including across reorders);
        - rows without an id get a fresh UUID v4.

        ``previous`` is accepted for symmetry with the spec but the actual
        merge is value-based, not previous-aware: the client either submits
        an id or not, and we don't try to fingerprint-match unidentified
        rows back to old rows. That keeps the algorithm simple and matches
        the spec's "submit-without-id = treat as new" rule.
        """
        result = copy.deepcopy(incoming) if incoming else {}
        for key, spec in specs.specs.items():
            if not isinstance(spec, ParamSet) or spec.param_set is None:
                continue
            rows = result.get(key)
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                if not row.get(cls.ITEM_ID_KEY):
                    row[cls.ITEM_ID_KEY] = str(uuid.uuid4())
        return result

    # ------------------------------------------------------------------ #
    # Computed-key strip and merge
    # ------------------------------------------------------------------ #

    @classmethod
    def strip_computed_keys(
        cls, specs: ConfigSpecs, values: dict[str, Any]
    ) -> dict[str, Any]:
        """Drop keys whose ``spec.accepts_user_input is False`` (currently
        ``ComputedParam``). Recurses into ParamSet rows.

        This is an input-side defensive strip applied to incoming
        ``dto.values`` before validation. Computed values ARE stored
        (alongside user values, in the same ``Form.values`` JSON), but the
        evaluator is the only thing allowed to write them — clients never
        do, so we wipe any submitted entry before further processing.
        """
        if not values:
            return {} if values is None else values
        result: dict[str, Any] = {}
        for key, value in values.items():
            spec = specs.specs.get(key)
            if spec is not None and not spec.accepts_user_input:
                continue
            if (
                isinstance(spec, ParamSet)
                and spec.param_set is not None
                and isinstance(value, list)
            ):
                result[key] = [
                    cls._strip_paramset_row(spec.param_set, row)
                    for row in value
                    if isinstance(row, dict)
                ]
            else:
                result[key] = value
        return result

    @classmethod
    def _strip_paramset_row(
        cls, inner_specs: ConfigSpecs, row: dict[str, Any]
    ) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for k, v in row.items():
            if k == cls.ITEM_ID_KEY:
                out[k] = v
                continue
            spec = inner_specs.specs.get(k)
            if spec is not None and not spec.accepts_user_input:
                continue
            out[k] = v
        return out

    @classmethod
    def merge_computed(
        cls,
        specs: ConfigSpecs,
        user_values: dict[str, Any],
        computed: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge the outer-scope computed dict into ``user_values`` and
        return the union.

        Per-row ParamSet computed cells are populated in-place by
        ``ConfigSpecs.compute_values`` (see ``ComputedParam._evaluate_paramset_rows``),
        so this only needs to handle outer-scope keys. The result is the
        single dict that gets persisted to ``Form.values``.
        """
        result = copy.deepcopy(user_values) if user_values else {}
        for key, value in (computed or {}).items():
            spec = specs.specs.get(key)
            if spec is None or spec.accepts_user_input:
                # Outer-scope computed entries only — paramset rows already
                # carry their per-row computed values from compute_values.
                continue
            result[key] = value
        return result

    # ------------------------------------------------------------------ #
    # Validation
    # ------------------------------------------------------------------ #

    @classmethod
    def validate_with_specs(
        cls, specs: ConfigSpecs, values: dict[str, Any]
    ) -> None:
        """Run ``ParamSpec.validate(...)`` on every provided leaf.

        Missing mandatories DO NOT raise here — DRAFT save is allowed to
        be partial. The submit gate (``ConfigSpecs.mandatory_values_are_set``)
        runs separately when transitioning to SUBMITTED.

        ParamSet rows are validated row-by-row with ``__item_id`` stripped
        first, otherwise the inner dict validator flags it as an unknown key.
        """
        if not values:
            return
        for key, value in values.items():
            spec = specs.specs.get(key)
            if spec is None or not spec.accepts_user_input:
                continue
            if value is None:
                continue
            if isinstance(spec, ParamSet) and spec.param_set is not None:
                rows = value if isinstance(value, list) else []
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    inner = {
                        k: v for k, v in row.items() if k != cls.ITEM_ID_KEY
                    }
                    for inner_key, inner_value in inner.items():
                        inner_spec = spec.param_set.specs.get(inner_key)
                        if (
                            inner_spec is None
                            or not inner_spec.accepts_user_input
                            or inner_value is None
                        ):
                            continue
                        inner_spec.validate(inner_value)
            else:
                spec.validate(value)

    # ------------------------------------------------------------------ #
    # Diff
    # ------------------------------------------------------------------ #

    @classmethod
    def diff_values(
        cls,
        old: dict[str, Any] | None,
        new: dict[str, Any] | None,
    ) -> list[FormChangeEntry]:
        """Recursive diff producing one FormChangeEntry per leaf change.

        Field-path shape:
        - top-level scalar:        ``mass``
        - ParamSet item field:     ``samples[item_id=<uuid>].mass``
        - whole item add/remove:   ``samples[item_id=<uuid>]``

        Reorder = REMOVED + ADDED for the same ``__item_id`` (no MOVED).
        Status changes are appended by the caller, not here.
        """
        old = old or {}
        new = new or {}
        changes: list[FormChangeEntry] = []
        keys = set(old.keys()) | set(new.keys())
        for key in sorted(keys):
            old_val = old.get(key)
            new_val = new.get(key)
            if cls._is_paramset_value(old_val) or cls._is_paramset_value(new_val):
                changes.extend(cls._diff_paramset(key, old_val, new_val))
            else:
                changes.extend(cls._diff_scalar(key, old_val, new_val, key in old, key in new))
        return changes

    @classmethod
    def _is_paramset_value(cls, value: Any) -> bool:
        """A ParamSet value is a list of dicts; we identify it structurally
        rather than by spec lookup so the diff can run without a ConfigSpecs."""
        if not isinstance(value, list) or not value:
            return False
        return all(isinstance(item, dict) for item in value)

    @classmethod
    def _diff_scalar(
        cls,
        path: str,
        old_val: Any,
        new_val: Any,
        in_old: bool,
        in_new: bool,
    ) -> list[FormChangeEntry]:
        if not in_old and in_new:
            return [
                FormChangeEntry(
                    field_path=path,
                    action=FormChangeAction.FIELD_CREATED,
                    old_value=None,
                    new_value=new_val,
                )
            ]
        if in_old and not in_new:
            return [
                FormChangeEntry(
                    field_path=path,
                    action=FormChangeAction.FIELD_DELETED,
                    old_value=old_val,
                    new_value=None,
                )
            ]
        if old_val != new_val:
            return [
                FormChangeEntry(
                    field_path=path,
                    action=FormChangeAction.FIELD_UPDATED,
                    old_value=old_val,
                    new_value=new_val,
                )
            ]
        return []

    @classmethod
    def _diff_paramset(
        cls,
        key: str,
        old_val: Any,
        new_val: Any,
    ) -> list[FormChangeEntry]:
        old_rows: list[dict[str, Any]] = old_val if isinstance(old_val, list) else []
        new_rows: list[dict[str, Any]] = new_val if isinstance(new_val, list) else []

        old_by_id = {
            row.get(cls.ITEM_ID_KEY): row
            for row in old_rows
            if isinstance(row, dict) and row.get(cls.ITEM_ID_KEY)
        }
        new_by_id = {
            row.get(cls.ITEM_ID_KEY): row
            for row in new_rows
            if isinstance(row, dict) and row.get(cls.ITEM_ID_KEY)
        }

        changes: list[FormChangeEntry] = []

        for item_id in sorted(set(old_by_id) - set(new_by_id)):
            changes.append(
                FormChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=FormChangeAction.PARAMSET_ITEM_REMOVED,
                    old_value=cls._strip_id(old_by_id[item_id]),
                    new_value=None,
                )
            )
        for item_id in sorted(set(new_by_id) - set(old_by_id)):
            changes.append(
                FormChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=FormChangeAction.PARAMSET_ITEM_ADDED,
                    old_value=None,
                    new_value=cls._strip_id(new_by_id[item_id]),
                )
            )

        for item_id in sorted(set(old_by_id) & set(new_by_id)):
            old_row = old_by_id[item_id]
            new_row = new_by_id[item_id]
            inner_keys = (set(old_row.keys()) | set(new_row.keys())) - {cls.ITEM_ID_KEY}
            for inner_key in sorted(inner_keys):
                in_old = inner_key in old_row
                in_new = inner_key in new_row
                old_inner = old_row.get(inner_key)
                new_inner = new_row.get(inner_key)
                inner_path = f"{key}[item_id={item_id}].{inner_key}"
                changes.extend(
                    cls._diff_scalar(inner_path, old_inner, new_inner, in_old, in_new)
                )

        return changes

    @classmethod
    def _strip_id(cls, row: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in row.items() if k != cls.ITEM_ID_KEY}
