"""ParamSet.validate tests for __item_id identity reconciliation.

Spec: form_feature.md §7. Identity is a generic ConfigSpecs concern; it lives
on ParamSet so any ConfigSpecs consumer benefits, not just forms.
"""
import unittest
import uuid

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet
from gws_core.config.param.param_spec import FloatParam


def _paramset() -> ParamSet:
    return ParamSet(
        ConfigSpecs(
            {
                "mass": FloatParam(human_name="Mass"),
                "volume": FloatParam(human_name="Volume", optional=True),
            }
        )
    )


class TestParamSetItemId(unittest.TestCase):

    def test_mints_uuid_for_row_without_item_id(self):
        ps = _paramset()
        result = ps.validate([{"mass": 1.0, "volume": 0.5}])
        self.assertEqual(len(result), 1)
        self.assertIn(ConfigSpecs.ITEM_ID_KEY, result[0])
        uuid.UUID(result[0][ConfigSpecs.ITEM_ID_KEY])

    def test_mints_distinct_uuids_for_each_row(self):
        ps = _paramset()
        result = ps.validate(
            [{"mass": 1.0, "volume": 0.5}, {"mass": 2.0, "volume": 1.0}]
        )
        ids = [row[ConfigSpecs.ITEM_ID_KEY] for row in result]
        self.assertEqual(len(set(ids)), 2)

    def test_preserves_existing_item_id(self):
        ps = _paramset()
        existing = str(uuid.uuid4())
        result = ps.validate(
            [{ConfigSpecs.ITEM_ID_KEY: existing, "mass": 1.0, "volume": 0.5}]
        )
        self.assertEqual(result[0][ConfigSpecs.ITEM_ID_KEY], existing)

    def test_rejects_duplicate_item_ids_within_paramset(self):
        ps = _paramset()
        dup = str(uuid.uuid4())
        with self.assertRaises(ValueError):
            ps.validate(
                [
                    {ConfigSpecs.ITEM_ID_KEY: dup, "mass": 1.0, "volume": 0.5},
                    {ConfigSpecs.ITEM_ID_KEY: dup, "mass": 2.0, "volume": 1.0},
                ]
            )

    def test_validated_row_keeps_inner_values(self):
        ps = _paramset()
        result = ps.validate([{"mass": 1.5, "volume": 0.5}])
        self.assertEqual(result[0]["mass"], 1.5)
        self.assertEqual(result[0]["volume"], 0.5)

    def test_idempotent_round_trip(self):
        ps = _paramset()
        first = ps.validate([{"mass": 1.0, "volume": 0.5}])
        second = ps.validate(first)
        self.assertEqual(
            first[0][ConfigSpecs.ITEM_ID_KEY],
            second[0][ConfigSpecs.ITEM_ID_KEY],
        )

    def test_validate_does_not_mutate_input(self):
        ps = _paramset()
        existing = str(uuid.uuid4())
        input_rows = [{ConfigSpecs.ITEM_ID_KEY: existing, "mass": 1.0, "volume": 0.5}]
        ps.validate(input_rows)
        # Caller's dicts must be untouched.
        self.assertEqual(input_rows[0][ConfigSpecs.ITEM_ID_KEY], existing)
        self.assertEqual(input_rows[0]["mass"], 1.0)


if __name__ == "__main__":
    unittest.main()
