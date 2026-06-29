"""ParamSet tests for default_rows, default_rows_mode and min_number_of_occurrences.

Default rows are POSITIONAL and carry NO __item_id: they behave like rows with
no default at all (ids are minted on validation). The LOCK_PROVIDED mode pins the
provided cells of the preset at index i onto the incoming row at index i.
"""
import unittest

from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_set import ParamSet, ParamSetDefaultRowsMode
from gws_core.config.param.param_spec import FloatParam, StrParam
from gws_core.core.exception.exceptions.bad_request_exception import BadRequestException

LOCK = ParamSetDefaultRowsMode.LOCK_PROVIDED


def _specs() -> ConfigSpecs:
    return ConfigSpecs(
        {
            "name": StrParam(human_name="Name"),
            "value": FloatParam(human_name="Value", optional=True),
        }
    )


def _preset_paramset(lock: bool = False) -> ParamSet:
    return ParamSet(
        _specs(),
        default_rows_mode=LOCK if lock else ParamSetDefaultRowsMode.EDITABLE,
        default_rows=[
            {"name": "morning"},
            {"name": "afternoon"},
            {"name": "evening"},
        ],
    )


class TestParamSetDefaultRows(unittest.TestCase):

    # ----- default_rows -------------------------------------------------- #

    def test_default_value_returns_preset_rows(self):
        ps = _preset_paramset()
        default = ps.get_default_value()
        self.assertEqual([r["name"] for r in default], ["morning", "afternoon", "evening"])

    def test_default_rows_merge_inner_defaults(self):
        ps = _preset_paramset()
        default = ps.get_default_value()
        # 'value' was not provided in the preset -> falls back to its default
        for row in default:
            self.assertIn("value", row)

    def test_default_value_carries_no_item_id(self):
        # presets are positional; ids are minted on validation, not on the default
        ps = _preset_paramset()
        for row in ps.get_default_value():
            self.assertNotIn(ConfigSpecs.ITEM_ID_KEY, row)

    def test_get_default_value_returns_copies(self):
        ps = _preset_paramset()
        first = ps.get_default_value()
        first[0]["name"] = "mutated"
        # spec presets must be untouched
        self.assertEqual(ps.get_default_value()[0]["name"], "morning")

    # ----- min_number_of_occurrences ------------------------------------- #

    def test_min_occurrences_enforced(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=2)
        with self.assertRaises(BadRequestException):
            ps.validate([{"name": "a"}])

    def test_min_occurrences_ok(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=2)
        result = ps.validate([{"name": "a"}, {"name": "b"}])
        self.assertEqual(len(result), 2)

    # ----- max vs min consistency ---------------------------------------- #

    def test_max_lower_than_min_rejected(self):
        with self.assertRaises(BadRequestException):
            ParamSet(_specs(), min_number_of_occurrences=3, max_number_of_occurrences=2)

    def test_max_equal_to_min_allowed(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=2, max_number_of_occurrences=2)
        self.assertEqual(ps.max_number_of_occurrences, 2)

    def test_negative_max_is_no_limit(self):
        # negative / None max means "no upper limit" -> never inconsistent
        ParamSet(_specs(), min_number_of_occurrences=3, max_number_of_occurrences=-1)
        ParamSet(_specs(), min_number_of_occurrences=3, max_number_of_occurrences=None)

    def test_max_vs_min_checked_on_load_when_validating(self):
        dto = ParamSet(_specs(), min_number_of_occurrences=1).to_dto()
        dto.additional_info["min_number_of_occurrences"] = 3
        dto.additional_info["max_number_of_occurrences"] = 2
        with self.assertRaises(BadRequestException):
            ParamSet.load_from_dto(dto, validate=True)

    # ----- optional is derived from min_number_of_occurrences ------------ #

    def test_default_min_is_one_and_not_optional(self):
        ps = ParamSet(_specs())
        self.assertEqual(ps.min_number_of_occurrences, 1)
        self.assertFalse(ps.optional)
        # a single empty default row, like a non-optional ParamSet
        self.assertEqual(len(ps.get_default_value()), 1)

    def test_min_zero_makes_optional(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=0)
        self.assertTrue(ps.optional)
        # optional -> default value is an empty array
        self.assertEqual(ps.get_default_value(), [])

    def test_min_one_rejects_empty(self):
        ps = ParamSet(_specs())  # default min == 1
        with self.assertRaises(BadRequestException):
            ps.validate([])

    def test_min_zero_accepts_empty(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=0)
        self.assertEqual(ps.validate([]), [])

    def test_optional_round_trips_through_dto(self):
        ps = ParamSet(_specs(), min_number_of_occurrences=0)
        reloaded = ParamSet.load_from_dto(ps.to_dto())
        self.assertTrue(reloaded.optional)
        self.assertEqual(reloaded.min_number_of_occurrences, 0)

    # ----- default_rows_mode = LOCK_PROVIDED ----------------------------- #

    def test_lock_requires_default_rows(self):
        with self.assertRaises(BadRequestException):
            ParamSet(_specs(), default_rows_mode=LOCK)

    def test_default_value_ignores_occurrence_bounds_on_load(self):
        # Regression: the default value must NOT be checked against
        # min_number_of_occurrences (regardless of mode). A default holding 0
        # rows under min=1 used to raise "Invalid default value ... the minimum
        # number of elements is 1." on load_from_dto(validate=True).
        for mode in (ParamSetDefaultRowsMode.EDITABLE, LOCK):
            with self.subTest(mode=mode):
                ps = ParamSet(
                    _specs(),
                    default_rows=[{"name": "morning"}],
                    default_rows_mode=mode,
                    min_number_of_occurrences=1,
                )
                # the default value (one preset row) is fewer than nothing here,
                # but the round-trip through a serialized spec is the real path:
                dto = ps.to_dto()
                # force a 0-row default to exercise the relaxed check explicitly
                dto.default_value = []
                reloaded = ParamSet.load_from_dto(dto, validate=True)
                self.assertEqual(reloaded.min_number_of_occurrences, 1)

    def test_user_value_still_enforces_occurrence_bounds(self):
        # The relaxation is scoped to the DEFAULT value; a user-submitted value
        # is still validated against min_number_of_occurrences.
        ps = ParamSet(_specs(), min_number_of_occurrences=1)
        with self.assertRaises(BadRequestException):
            ps.validate([])

    def test_default_value_tolerates_missing_mandatory_on_load(self):
        # Regression: a default row that leaves a mandatory inner field (here
        # 'name') unset must NOT raise "the mandatory config 'Name' is missing."
        # — the user fills it; the default only pre-fills what it provides.
        ps = ParamSet(_specs())
        dto = ps.to_dto()
        dto.default_value = [{"value": 1.0}]  # 'name' (mandatory) omitted
        reloaded = ParamSet.load_from_dto(dto, validate=True)
        self.assertEqual(reloaded.default_value, [{"value": 1.0}])

    def test_default_value_tolerates_none_cells_on_load(self):
        ps = ParamSet(_specs())
        dto = ps.to_dto()
        dto.default_value = [{"name": None, "value": None}]
        ParamSet.load_from_dto(dto, validate=True)  # must not raise

    def test_default_value_rejects_incompatible_value_on_load(self):
        # A PROVIDED value that is incompatible (wrong type) is still rejected.
        ps = ParamSet(_specs())
        dto = ps.to_dto()
        dto.default_value = [{"value": "not-a-float"}]
        with self.assertRaises(BadRequestException):
            ParamSet.load_from_dto(dto, validate=True)

    def test_no_row_duplication_on_validate(self):
        # Regression: the client sends the 3 preset rows back WITHOUT ids
        # (as the front end does). The result must be exactly 3 rows, not 6.
        ps = _preset_paramset(lock=True)
        result = ps.validate(
            [{"name": "morning"}, {"name": "afternoon"}, {"name": "evening"}]
        )
        self.assertEqual(len(result), 3)
        self.assertEqual([r["name"] for r in result], ["morning", "afternoon", "evening"])

    def test_locked_values_reasserted_on_edit_attempt(self):
        # client sends rows WITHOUT ids and tries to change the locked cell at row 0
        ps = _preset_paramset(lock=True)
        result = ps.validate(
            [
                {"name": "HACKED", "value": 99.0},
                {"name": "afternoon"},
                {"name": "evening"},
            ]
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "morning")  # locked cell restored

    def test_validated_rows_get_fresh_uuids(self):
        # ids are minted exactly like the no-default case
        ps = _preset_paramset(lock=True)
        result = ps.validate(
            [{"name": "morning"}, {"name": "afternoon"}, {"name": "evening"}]
        )
        ids = [r[ConfigSpecs.ITEM_ID_KEY] for r in result]
        self.assertEqual(len(set(ids)), 3)
        for item_id in ids:
            self.assertFalse(item_id.startswith("__default_"))

    def test_unlocked_presets_editable(self):
        # without the lock, presets are pure pre-fill and fully editable
        ps = _preset_paramset(lock=False)
        result = ps.validate([{"name": "changed"}])
        self.assertEqual(result[0]["name"], "changed")

    def test_user_can_add_rows_with_lock(self):
        ps = _preset_paramset(lock=True)
        result = ps.validate(
            [
                {"name": "morning"},
                {"name": "afternoon"},
                {"name": "evening"},
                {"name": "night"},  # extra row beyond the presets -> not locked
            ]
        )
        self.assertEqual(len(result), 4)
        self.assertEqual(result[3]["name"], "night")

    def test_locked_user_can_fill_not_provided_cell(self):
        # preset row 0 provides only 'value' (locked); 'name' is empty and editable
        ps = ParamSet(
            _specs(),
            default_rows=[{"value": 1.0}],
            default_rows_mode=LOCK,
        )
        result = ps.validate([{"name": "user-filled", "value": 99.0}])
        row = result[0]
        self.assertEqual(row["value"], 1.0)        # provided -> locked
        self.assertEqual(row["name"], "user-filled")  # not provided -> editable

    def test_locked_only_provided_cells_pinned(self):
        # preset provides only 'name' -> 'value' stays fully editable
        ps = ParamSet(
            _specs(),
            default_rows=[{"name": "morning"}],
            default_rows_mode=LOCK,
        )
        result = ps.validate([{"name": "HACKED", "value": 5.0}])
        row = result[0]
        self.assertEqual(row["name"], "morning")  # provided -> locked
        self.assertEqual(row["value"], 5.0)        # not provided -> editable

    def test_locked_null_cell_does_not_clobber_user_value(self):
        # Regression (bug report): a preset cell whose value is None is NOT a
        # real lock — it must keep the user's value, not overwrite it with null.
        ps = ParamSet(
            ConfigSpecs({"name": StrParam(human_name="Name"),
                         "price": FloatParam(human_name="Price")}),
            # row1 provides name='Apple' but price=None ; row2 provides price=15
            # but name=None. The None cells must stay user-editable.
            default_rows=[
                {"name": "Banana", "price": 10},
                {"name": "Apple", "price": None},
                {"name": None, "price": 15},
            ],
            default_rows_mode=LOCK,
        )
        # user fills every cell
        result = ps.validate(
            [
                {"name": "Banana", "price": 10},
                {"name": "Apple", "price": 8},
                {"name": "Cool", "price": 15},
            ]
        )
        self.assertEqual(len(result), 3)
        # locked (non-null) cells are pinned
        self.assertEqual(result[0]["name"], "Banana")
        self.assertEqual(result[0]["price"], 10)
        self.assertEqual(result[1]["name"], "Apple")
        self.assertEqual(result[2]["price"], 15)
        # null preset cells kept the USER value (this is what regressed)
        self.assertEqual(result[1]["price"], 8)
        self.assertEqual(result[2]["name"], "Cool")

    # ----- default_rows validation at construction ----------------------- #

    def test_unknown_field_in_default_row_raises(self):
        with self.assertRaises(BadRequestException):
            ParamSet(_specs(), default_rows=[{"naem": "morning"}])  # typo

    def test_bad_leaf_value_in_default_row_raises(self):
        with self.assertRaises(BadRequestException):
            ParamSet(_specs(), default_rows=[{"name": "ok", "value": "not-a-float"}])

    def test_locked_missing_mandatory_allowed(self):
        # lock pins only provided cells; the user fills the rest -> no raise even
        # when a mandatory ('name') is left out of the locked preset
        ps = ParamSet(
            _specs(),
            default_rows=[{"value": 1.0}],
            default_rows_mode=LOCK,
        )
        self.assertEqual(len(ps.get_default_value()), 1)

    def test_unlocked_missing_mandatory_allowed(self):
        ps = ParamSet(_specs(), default_rows=[{"value": 1.0}])
        self.assertEqual(len(ps.get_default_value()), 1)

    # ----- lenient validation: only user-fillable cells error ------------ #

    def test_lenient_locked_cell_not_reported_missing(self):
        # preset row 0 locks 'name'; user leaves it null in the payload.
        # The locked value is pinned before validation, so 'name' must NOT
        # appear as a missing-mandatory error. 'value' (user-fillable, null)
        # is optional here, so no error at all on row 0.
        ps = ParamSet(_specs(), default_rows=[{"name": "morning"}], default_rows_mode=LOCK)
        res = ps.validate_lenient([{"name": None, "value": None}])
        self.assertEqual(res.rows[0]["name"], "morning")

    # ----- DTO round-trip ------------------------------------------------ #

    def test_dto_round_trip_preserves_features(self):
        ps = _preset_paramset(lock=True)
        ps.min_number_of_occurrences = 1
        dto = ps.to_dto()
        reloaded = ParamSet.load_from_dto(dto)
        self.assertEqual(reloaded.default_rows_mode, LOCK)
        self.assertEqual(reloaded.min_number_of_occurrences, 1)
        self.assertEqual(
            [r["name"] for r in reloaded.get_default_value()],
            ["morning", "afternoon", "evening"],
        )
        # presets still carry no id after reload
        for row in reloaded.get_default_value():
            self.assertNotIn(ConfigSpecs.ITEM_ID_KEY, row)
        # lock enforcement still works after reload (no duplication)
        result = reloaded.validate(
            [{"name": "HACKED"}, {"name": "afternoon"}, {"name": "evening"}]
        )
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["name"], "morning")

    def test_dto_default_value_has_no_ids(self):
        # the serialized default_value (what the front consumes) carries no ids
        ps = _preset_paramset(lock=True)
        dto = ps.to_dto()
        for row in dto.default_value:
            self.assertNotIn(ConfigSpecs.ITEM_ID_KEY, row)

    def test_dto_serializes_mode_as_string(self):
        ps = _preset_paramset(lock=True)
        dto = ps.to_dto()
        self.assertEqual(dto.additional_info["default_rows_mode"], "lock_provided")

    def test_load_legacy_lock_default_rows_boolean(self):
        # specs serialized before the enum carry the legacy boolean -> coerced
        ps = _preset_paramset(lock=True)
        dto = ps.to_dto()
        del dto.additional_info["default_rows_mode"]
        dto.additional_info["lock_default_rows"] = True
        reloaded = ParamSet.load_from_dto(dto)
        self.assertEqual(reloaded.default_rows_mode, LOCK)

    def test_load_legacy_lock_default_rows_false(self):
        ps = _preset_paramset(lock=False)
        dto = ps.to_dto()
        del dto.additional_info["default_rows_mode"]
        dto.additional_info["lock_default_rows"] = False
        reloaded = ParamSet.load_from_dto(dto)
        self.assertEqual(reloaded.default_rows_mode, ParamSetDefaultRowsMode.EDITABLE)

    # ----- clone_with_inner_specs ---------------------------------------- #

    def test_clone_with_inner_specs_copies_all_attributes(self):
        ps = ParamSet(
            _specs(),
            default_rows=[{"name": "morning"}],
            default_rows_mode=LOCK,
            min_number_of_occurrences=0,  # makes it optional
            max_number_of_occurrences=5,
            human_name="Slots",
            short_description="the slots",
        )
        new_inner = ConfigSpecs({"name": StrParam(human_name="Name")})
        clone = ps.clone_with_inner_specs(new_inner)

        self.assertIs(clone.param_set, new_inner)  # inner replaced
        self.assertEqual(clone.default_rows_mode, LOCK)
        self.assertEqual(clone.min_number_of_occurrences, 0)
        self.assertEqual(clone.max_number_of_occurrences, 5)
        self.assertEqual(clone.optional, True)  # derived from min == 0
        self.assertEqual(clone.human_name, "Slots")
        self.assertEqual(clone.short_description, "the slots")
        self.assertEqual(clone.default_rows, ps.default_rows)

    def test_clone_with_inner_specs_no_default_rows(self):
        ps = ParamSet(_specs())
        clone = ps.clone_with_inner_specs(ConfigSpecs({"x": StrParam()}))
        self.assertIsNone(clone.default_rows)
        self.assertEqual(clone.default_rows_mode, ParamSetDefaultRowsMode.EDITABLE)

    def test_clone_default_rows_is_independent_copy(self):
        ps = ParamSet(_specs(), default_rows=[{"name": "morning"}], default_rows_mode=LOCK)
        clone = ps.clone_with_inner_specs(_specs())
        clone.default_rows[0]["name"] = "mutated"
        self.assertEqual(ps.default_rows[0]["name"], "morning")


if __name__ == "__main__":
    unittest.main()
