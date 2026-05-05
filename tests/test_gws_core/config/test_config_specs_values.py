"""Pure-function tests for the values-layer helpers on ConfigSpecs —
strip_computed_keys, validate_values, merge_computed, diff_values.

Run without a database; ConfigSpecs is
stateless.
"""

import unittest
import uuid

from gws_core.config.config_change_dto import ConfigChangeAction
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.computed.computed_param import ComputedParam
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam, StrParam
from gws_core.form.form_dto import FormChangeAction


def _scalar_specs() -> ConfigSpecs:
    return ConfigSpecs(
        {
            "name": StrParam(human_name="Name"),
            "mass": FloatParam(human_name="Mass", optional=True),
        }
    )


def _paramset_specs() -> ConfigSpecs:
    return ConfigSpecs(
        {
            "samples": ParamSet(
                ConfigSpecs(
                    {
                        "mass": FloatParam(human_name="Mass"),
                        "volume": FloatParam(human_name="Volume", optional=True),
                    }
                ),
            ),
        }
    )


def _paramset_with_computed_specs() -> ConfigSpecs:
    return ConfigSpecs(
        {
            "samples": ParamSet(
                ConfigSpecs(
                    {
                        "mass": FloatParam(human_name="Mass"),
                        "volume": FloatParam(human_name="Volume"),
                        "density": ComputedParam(expression="mass / volume", result_type="float"),
                    }
                ),
            ),
            "total_mass": ComputedParam(expression="sum(samples[].mass)", result_type="float"),
        }
    )


class TestFormChangeActionStorageCompat(unittest.TestCase):
    """Locks the persisted JSON shape: FormChangeAction members that exist on
    ConfigChangeAction MUST share the same string value, otherwise existing
    FormSaveEvent rows would deserialize incorrectly."""

    def test_string_values_match(self):
        for member in (
            "FIELD_CREATED",
            "FIELD_UPDATED",
            "FIELD_DELETED",
            "PARAMSET_ITEM_ADDED",
            "PARAMSET_ITEM_REMOVED",
        ):
            self.assertEqual(
                FormChangeAction[member].value,
                ConfigChangeAction[member].value,
                f"{member} value drift would break stored FormSaveEvent.changes JSON",
            )


class TestStripComputedKeys(unittest.TestCase):
    def test_strips_outer_computed(self):
        specs = _paramset_with_computed_specs()
        # Client tries to write to total_mass — should be stripped.
        result = specs.strip_computed_keys(
            {"samples": [{"mass": 1.0, "volume": 0.5}], "total_mass": 999.0},
        )
        self.assertNotIn("total_mass", result)
        self.assertEqual(result["samples"], [{"mass": 1.0, "volume": 0.5}])

    def test_strips_per_row_computed(self):
        specs = _paramset_with_computed_specs()
        result = specs.strip_computed_keys(
            {
                "samples": [
                    {"__item_id": "abc", "mass": 1.0, "volume": 0.5, "density": 999.0},
                ],
            },
        )
        row = result["samples"][0]
        self.assertNotIn("density", row)
        self.assertEqual(row["__item_id"], "abc")
        self.assertEqual(row["mass"], 1.0)


class TestValidateValues(unittest.TestCase):
    def test_valid_values_pass(self):
        specs = _scalar_specs()
        result = specs.validate_values({"name": "x", "mass": 1.5})
        self.assertEqual(result["name"], "x")
        self.assertEqual(result["mass"], 1.5)

    def test_invalid_type_raises(self):
        specs = _scalar_specs()
        with self.assertRaises(Exception):
            specs.validate_values({"name": "x", "mass": "not a float"})

    def test_paramset_row_validation_strips_item_id(self):
        specs = _paramset_specs()
        existing_id = str(uuid.uuid4())
        result = specs.validate_values(
            {
                "samples": [
                    {"__item_id": existing_id, "mass": 1.0, "volume": 0.5},
                ],
            },
        )
        # The id is preserved on the validated row (round-trip through ParamSet).
        self.assertEqual(result["samples"][0]["__item_id"], existing_id)
        self.assertEqual(result["samples"][0]["mass"], 1.0)

    def test_paramset_row_without_item_id_gets_one_minted(self):
        specs = _paramset_specs()
        result = specs.validate_values(
            {"samples": [{"mass": 1.0, "volume": 0.5}]},
        )
        row = result["samples"][0]
        self.assertIn("__item_id", row)
        uuid.UUID(row["__item_id"])  # raises if not a valid UUID

    def test_missing_mandatory_does_not_raise(self):
        specs = _scalar_specs()
        # name is mandatory but unset — DRAFT save allows this.
        specs.validate_values({"mass": 1.5})


class TestMergeComputed(unittest.TestCase):
    def test_merges_outer_computed_into_union(self):
        specs = _paramset_with_computed_specs()
        user_values = {"samples": [{"__item_id": "x", "mass": 1.0, "volume": 0.5}]}
        computed = {"total_mass": 1.0}
        result = specs.merge_computed(user_values, computed)
        self.assertEqual(result["total_mass"], 1.0)
        # User values preserved.
        self.assertEqual(result["samples"][0]["mass"], 1.0)

    def test_does_not_merge_user_keys(self):
        specs = _paramset_with_computed_specs()
        user_values = {"samples": []}
        computed = {"name": "should not appear"}  # not a computed key
        result = specs.merge_computed(user_values, computed)
        self.assertNotIn("name", result)


class TestDiffValues(unittest.TestCase):
    def test_field_created(self):
        changes = ConfigSpecs.diff_values({}, {"name": "x"})
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.field_path, "name")
        self.assertEqual(c.action, ConfigChangeAction.FIELD_CREATED)
        self.assertIsNone(c.old_value)
        self.assertEqual(c.new_value, "x")

    def test_field_updated(self):
        changes = ConfigSpecs.diff_values({"name": "x"}, {"name": "y"})
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.action, ConfigChangeAction.FIELD_UPDATED)
        self.assertEqual(c.old_value, "x")
        self.assertEqual(c.new_value, "y")

    def test_field_deleted(self):
        changes = ConfigSpecs.diff_values({"name": "x"}, {})
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0].action, ConfigChangeAction.FIELD_DELETED)

    def test_field_unchanged_no_entry(self):
        changes = ConfigSpecs.diff_values({"name": "x"}, {"name": "x"})
        self.assertEqual(changes, [])

    def test_paramset_item_added(self):
        new_id = str(uuid.uuid4())
        changes = ConfigSpecs.diff_values(
            {"samples": []},
            {"samples": [{"__item_id": new_id, "mass": 1.0}]},
        )
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.action, ConfigChangeAction.PARAMSET_ITEM_ADDED)
        self.assertEqual(c.field_path, f"samples[item_id={new_id}]")
        self.assertEqual(c.new_value, {"mass": 1.0})

    def test_paramset_item_removed(self):
        old_id = str(uuid.uuid4())
        changes = ConfigSpecs.diff_values(
            {"samples": [{"__item_id": old_id, "mass": 1.0}]},
            {"samples": []},
        )
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.action, ConfigChangeAction.PARAMSET_ITEM_REMOVED)

    def test_paramset_item_field_updated(self):
        item_id = str(uuid.uuid4())
        changes = ConfigSpecs.diff_values(
            {"samples": [{"__item_id": item_id, "mass": 1.0}]},
            {"samples": [{"__item_id": item_id, "mass": 2.0}]},
        )
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.action, ConfigChangeAction.FIELD_UPDATED)
        self.assertEqual(c.field_path, f"samples[item_id={item_id}].mass")
        self.assertEqual(c.old_value, 1.0)
        self.assertEqual(c.new_value, 2.0)

    def test_paramset_pure_reorder_no_field_updates(self):
        a = str(uuid.uuid4())
        b = str(uuid.uuid4())
        old = {
            "samples": [
                {"__item_id": a, "mass": 1.0},
                {"__item_id": b, "mass": 2.0},
            ]
        }
        new = {
            "samples": [
                {"__item_id": b, "mass": 2.0},
                {"__item_id": a, "mass": 1.0},
            ]
        }
        changes = ConfigSpecs.diff_values(old, new)
        self.assertEqual(changes, [])

    def test_paramset_reorder_plus_edit(self):
        a = str(uuid.uuid4())
        b = str(uuid.uuid4())
        old = {
            "samples": [
                {"__item_id": a, "mass": 1.0},
                {"__item_id": b, "mass": 2.0},
            ]
        }
        new = {
            "samples": [
                {"__item_id": b, "mass": 2.0},
                {"__item_id": a, "mass": 9.9},
            ]
        }
        changes = ConfigSpecs.diff_values(old, new)
        self.assertEqual(len(changes), 1)
        c = changes[0]
        self.assertEqual(c.action, ConfigChangeAction.FIELD_UPDATED)
        self.assertEqual(c.field_path, f"samples[item_id={a}].mass")


if __name__ == "__main__":
    unittest.main()
