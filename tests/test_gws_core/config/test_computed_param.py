from typing import cast
from unittest import TestCase

from gws_core import (
    BadRequestException,
    ComputedParam,
    ConfigParams,
    ConfigSpecs,
    FloatParam,
    IntParam,
    ParamSet,
    StrParam,
    Task,
    TaskInputs,
    TaskOutputs,
    TaskRunner,
    task_decorator,
)
from gws_core.config.config_exceptions import MissingConfigsException
from gws_core.config.param.computed.computed_param_evaluator import (
    ComputedParamEvaluationError,
    ConfigSpecsEvaluator,
)
from gws_core.config.param.param_spec_helper import ParamSpecHelper
from gws_core.config.param.param_types import ParamSpecType


@task_decorator("ComputedParamTask")
class ComputedParamTask(Task):
    """Task that exposes a ComputedParam in its config_specs and stashes the
    resolved value somewhere the test can read it."""

    config_specs: ConfigSpecs = ConfigSpecs(
        {
            "mass": FloatParam(),
            "volume": FloatParam(),
            "density": ComputedParam(expression="@mass / @volume"),
        }
    )

    received_density: float | None = None

    def run(self, params: ConfigParams, inputs: TaskInputs) -> TaskOutputs:
        ComputedParamTask.received_density = params["density"]
        return {}


# test_computed_param
class TestComputedParamEvaluator(TestCase):
    def setUp(self) -> None:
        self.ev = ConfigSpecsEvaluator()

    def test_arithmetic(self) -> None:
        self.assertEqual(self.ev.evaluate("1 + 2 * 3", {}), 7)
        self.assertEqual(self.ev.evaluate("(1 + 2) * 3", {}), 9)
        self.assertEqual(self.ev.evaluate("10 // 3", {}), 3)
        self.assertEqual(self.ev.evaluate("10 % 3", {}), 1)
        self.assertEqual(self.ev.evaluate("2 ** 8", {}), 256)

    def test_comparisons_and_booleans(self) -> None:
        self.assertTrue(
            self.ev.evaluate("@a > @b and @c < @d", {"a": 5, "b": 3, "c": 1, "d": 2})
        )
        self.assertFalse(self.ev.evaluate("not (1 == 1)", {}))
        self.assertTrue(self.ev.evaluate("@a == 1 or @b == 2", {"a": 0, "b": 2}))

    def test_field_reference(self) -> None:
        self.assertEqual(self.ev.evaluate("@mass / @volume", {"mass": 6.0, "volume": 2.0}), 3.0)

    def test_bare_identifier_is_not_a_field_reference(self) -> None:
        # Without the leading `@`, `mass` is treated as a (non-existent) function
        # name / undefined name, not as a field reference — the value in scope
        # is ignored.
        with self.assertRaises(ComputedParamEvaluationError) as ctx:
            self.ev.evaluate("mass + 1", {"mass": 5})
        self.assertIn("@mass", str(ctx.exception))

    def test_field_named_like_a_function_resolves_via_sigil(self) -> None:
        # A field literally named `sum`: `@sum` is the field; `sum(...)` the func.
        self.assertEqual(self.ev.evaluate("@sum + 1", {"sum": 4}), 5)
        self.assertEqual(self.ev.evaluate("sum(@values)", {"values": [1, 2, 3]}), 6)

    def test_division_by_zero(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError) as ctx:
            self.ev.evaluate("@a / @b", {"a": 1, "b": 0})
        self.assertIn("Division by zero", str(ctx.exception))

    def test_unknown_reference(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError) as ctx:
            self.ev.evaluate("@xyz + 1", {})
        self.assertIn("xyz", str(ctx.exception))

    def test_attribute_access_disallowed(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            self.ev.evaluate("@a.b", {"a": "value"})

    def test_function_not_in_whitelist(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError) as ctx:
            self.ev.evaluate("len([1, 2])", {})
        self.assertIn("Function not allowed", str(ctx.exception))

    def test_lambda_disallowed(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            self.ev.evaluate("(lambda x: x)(1)", {})

    def test_numeric_functions(self) -> None:
        rows = {"samples": [{"x": 1.0}, {"x": 2.0}, {"x": 3.0}, {"x": 4.0}]}
        self.assertEqual(self.ev.evaluate("sum(@samples[].x)", {}, paramset_rows=rows), 10.0)
        self.assertEqual(self.ev.evaluate("mean(@samples[].x)", {}, paramset_rows=rows), 2.5)
        self.assertEqual(self.ev.evaluate("median(@samples[].x)", {}, paramset_rows=rows), 2.5)
        self.assertEqual(self.ev.evaluate("min(@samples[].x)", {}, paramset_rows=rows), 1.0)
        self.assertEqual(self.ev.evaluate("max(@samples[].x)", {}, paramset_rows=rows), 4.0)
        self.assertEqual(self.ev.evaluate("count(@samples[].x)", {}, paramset_rows=rows), 4)
        # stddev requires >=2
        self.assertGreater(self.ev.evaluate("stddev(@samples[].x)", {}, paramset_rows=rows), 0)
        self.assertEqual(self.ev.evaluate("abs(-5)", {}), 5)
        self.assertEqual(self.ev.evaluate("round(1.2345, 2)", {}), 1.23)
        self.assertEqual(self.ev.evaluate("sqrt(9)", {}), 3.0)
        self.assertEqual(self.ev.evaluate("pow(2, 10)", {}), 1024)

    def test_if(self) -> None:
        self.assertEqual(self.ev.evaluate("if(@a > 0, @a, -@a)", {"a": -3}), 3)
        self.assertEqual(self.ev.evaluate("if(@a > 0, @a, -@a)", {"a": 3}), 3)
        # nested
        self.assertEqual(
            self.ev.evaluate("if(@a > 0, if(@b > 0, 1, 2), 3)", {"a": 1, "b": -1}),
            2,
        )

    def test_concat_scalars(self) -> None:
        self.assertEqual(
            self.ev.evaluate('concat(@first, " ", @last)', {"first": "Bob", "last": "Lee"}),
            "Bob Lee",
        )

    def test_concat_list(self) -> None:
        self.assertEqual(
            self.ev.evaluate("concat(@items)", {"items": ["a", "b", "c"]}),
            "abc",
        )

    def test_concat_list_with_separator(self) -> None:
        self.assertEqual(
            self.ev.evaluate('concat(@items, sep=", ")', {"items": ["a", "b", "c"]}),
            "a, b, c",
        )

    def test_concat_coerces_non_strings(self) -> None:
        self.assertEqual(
            self.ev.evaluate('concat(@items, sep="-")', {"items": [1, 2, 3]}),
            "1-2-3",
        )

    def test_concat_skips_none(self) -> None:
        self.assertEqual(
            self.ev.evaluate('concat(@items, sep="|")', {"items": ["a", None, "b"]}),
            "a||b",
        )

    def test_aggregate_over_empty_paramset_raises(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            self.ev.evaluate("mean(@samples[].x)", {}, paramset_rows={"samples": []})

    def test_stddev_with_one_value_raises(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            self.ev.evaluate("stddev(@samples[].x)", {}, paramset_rows={"samples": [{"x": 1.0}]})

    def test_unknown_paramset_key(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            self.ev.evaluate("sum(@unknown[].x)", {}, paramset_rows={})

    def test_extract_referenced_keys(self) -> None:
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys("@mass / @volume"),
            {"mass", "volume"},
        )
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys("sum(@samples[].mass)"),
            {"samples"},
        )
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys('concat(@first, " ", @last)'),
            {"first", "last"},
        )
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys("if(@a > 0, @b, @c)"),
            {"a", "b", "c"},
        )
        # Function names are never references.
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys("sum(@a, @b)"),
            {"a", "b"},
        )
        # Aggregate key + a scalar sibling.
        self.assertEqual(
            ConfigSpecsEvaluator.extract_referenced_keys("sum(@samples[].mass) + @total"),
            {"samples", "total"},
        )

    def test_referenced_paramset_keys(self) -> None:
        self.assertEqual(
            ConfigSpecsEvaluator.referenced_paramset_keys("sum(@samples[].mass) + @total"),
            {"samples"},
        )
        self.assertEqual(
            ConfigSpecsEvaluator.referenced_paramset_keys("@a + @b"),
            set(),
        )

    def test_check_expression_syntax(self) -> None:
        # Well-formed expressions parse.
        ConfigSpecsEvaluator.check_expression_syntax("@a + sum(@b[].c)")
        ConfigSpecsEvaluator.check_expression_syntax("if(@a > 0, 1, 2)")
        # Empty / syntactically broken expressions raise.
        with self.assertRaises(ComputedParamEvaluationError):
            ConfigSpecsEvaluator.check_expression_syntax("  ")
        with self.assertRaises(ComputedParamEvaluationError):
            ConfigSpecsEvaluator.check_expression_syntax("@a +")

    def test_normalize_result_passes_supported_scalars(self) -> None:
        self.assertEqual(ConfigSpecsEvaluator.normalize_result(2), 2)
        self.assertEqual(ConfigSpecsEvaluator.normalize_result(2.5), 2.5)
        self.assertEqual(ConfigSpecsEvaluator.normalize_result("x"), "x")
        self.assertEqual(ConfigSpecsEvaluator.normalize_result(True), True)

    def test_normalize_result_none(self) -> None:
        self.assertIsNone(ConfigSpecsEvaluator.normalize_result(None))

    def test_normalize_result_rejects_unsupported_type(self) -> None:
        with self.assertRaises(ComputedParamEvaluationError):
            ConfigSpecsEvaluator.normalize_result([1, 2, 3])


# test_computed_param
class TestComputedParamSpec(TestCase):
    def test_constructor_validates_arguments(self) -> None:
        with self.assertRaises(BadRequestException):
            ComputedParam(expression="")
        with self.assertRaises(BadRequestException):
            ComputedParam(expression="   ")

    def test_accepts_user_input_is_false(self) -> None:
        spec = ComputedParam(expression="@a + @b")
        self.assertFalse(spec.accepts_user_input)
        self.assertTrue(spec.optional)
        self.assertIsNone(spec.get_default_value())

    def test_validate_rejects_non_null_value(self) -> None:
        spec = ComputedParam(expression="@a + @b")
        # None passes through (used as the input-pass placeholder).
        self.assertIsNone(spec.validate(None))
        with self.assertRaises(BadRequestException):
            spec.validate(1.0)

    def test_dto_round_trip(self) -> None:
        spec = ComputedParam(
            expression="@mass / @volume",
            human_name="Density",
            short_description="Computed density",
        )
        dto = spec.to_dto()
        self.assertEqual(dto.type, ParamSpecType.COMPUTED)
        self.assertEqual(dto.additional_info["expression"], "@mass / @volume")

        loaded = cast(ComputedParam, ParamSpecHelper.create_param_spec_from_dto(dto))
        self.assertIsInstance(loaded, ComputedParam)
        self.assertEqual(loaded.expression, "@mass / @volume")
        self.assertFalse(loaded.accepts_user_input)


# test_computed_param
class TestComputedParamInConfigSpecs(TestCase):
    def test_outer_scope_evaluation(self) -> None:
        specs = ConfigSpecs(
            {
                "mass": FloatParam(),
                "volume": FloatParam(),
                "density": ComputedParam(expression="@mass / @volume"),
            }
        )
        params = specs.build_config_params({"mass": 6.0, "volume": 2.0})
        self.assertEqual(params["density"], 3.0)

    def test_per_row_inside_paramset(self) -> None:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(
                    ConfigSpecs(
                        {
                            "mass": FloatParam(),
                            "volume": FloatParam(),
                            "density": ComputedParam(
                                expression="@mass / @volume"
                            ),
                        }
                    )
                ),
            }
        )
        params = specs.build_config_params(
            {
                "samples": [
                    {"mass": 6.0, "volume": 2.0},
                    {"mass": 9.0, "volume": 3.0},
                ]
            }
        )
        self.assertEqual(params["samples"][0]["density"], 3.0)
        self.assertEqual(params["samples"][1]["density"], 3.0)

    def test_outer_scope_aggregate_over_paramset(self) -> None:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(ConfigSpecs({"mass": FloatParam()})),
                "total_mass": ComputedParam(
                    expression="sum(@samples[].mass)"
                ),
            }
        )
        params = specs.build_config_params(
            {"samples": [{"mass": 1.0}, {"mass": 2.0}, {"mass": 3.0}]}
        )
        self.assertEqual(params["total_mass"], 6.0)

    def test_field_named_like_a_function_is_not_a_blind_spot(self) -> None:
        # A ConfigSpecs key that collides with a whitelisted function name
        # (`sum`) is unambiguous now: `@sum` is the field. It is part of the
        # dependency graph (so check_config_specs passes) and evaluates.
        specs = ConfigSpecs(
            {
                "sum": FloatParam(),
                "doubled_sum": ComputedParam(expression="@sum + @sum"),
            }
        )
        specs.check_config_specs()
        params = specs.build_config_params({"sum": 4.0})
        self.assertEqual(params["doubled_sum"], 8.0)

    def test_evaluation_error_does_not_block_save(self) -> None:
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "b": FloatParam(),
                "ratio": ComputedParam(expression="@a / @b"),
                "double_a": ComputedParam(expression="@a * 2"),
            }
        )
        # b == 0 → ratio errors but double_a still evaluates.
        computed, errors = specs.compute_values({"a": 4.0, "b": 0.0})
        self.assertIsNone(computed["ratio"])
        self.assertEqual(computed["double_a"], 8.0)
        self.assertIn("ratio", errors)
        self.assertNotIn("double_a", errors)

    def test_client_submitted_value_is_stripped(self) -> None:
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "computed": ComputedParam(expression="@a * 2"),
            }
        )
        # Client tries to inject a value for `computed`; build_config_params
        # should strip it before validation and re-evaluate from `a`.
        params = specs.build_config_params({"a": 5.0, "computed": 999.0})
        self.assertEqual(params["computed"], 10.0)

    def test_computed_of_computed(self) -> None:
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "doubled": ComputedParam(expression="@a * 2"),
                "quadrupled": ComputedParam(expression="@doubled * 2"),
            }
        )
        params = specs.build_config_params({"a": 3.0})
        self.assertEqual(params["doubled"], 6.0)
        self.assertEqual(params["quadrupled"], 12.0)

    def test_cycle_detected_at_check_config_specs(self) -> None:
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "x": ComputedParam(expression="@y + 1"),
                "y": ComputedParam(expression="@x + 1"),
            }
        )
        with self.assertRaises(BadRequestException) as ctx:
            specs.check_config_specs()
        self.assertIn("Cycle", str(ctx.exception))

    def test_unknown_reference_rejected_at_check_config_specs(self) -> None:
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "bad": ComputedParam(expression="@a + @missing"),
            }
        )
        with self.assertRaises(BadRequestException) as ctx:
            specs.check_config_specs()
        self.assertIn("missing", str(ctx.exception))

    def test_self_reference_is_a_cycle(self) -> None:
        specs = ConfigSpecs(
            {
                "x": ComputedParam(expression="@x + 1"),
            }
        )
        with self.assertRaises(BadRequestException):
            specs.check_config_specs()

    def test_result_keeps_expression_natural_type(self) -> None:
        # Like a spreadsheet cell, the value keeps whatever type the formula
        # produces — no declared type, no coercion.
        specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "as_is": ComputedParam(expression="@a"),
                "as_int": ComputedParam(expression="round(@a)"),
                "as_str": ComputedParam(expression="concat(@a)"),
                "as_bool": ComputedParam(expression="@a > 0"),
            }
        )
        params = specs.build_config_params({"a": 2.7})
        self.assertEqual(params["as_is"], 2.7)
        self.assertEqual(params["as_int"], 3)
        self.assertEqual(params["as_str"], "2.7")
        self.assertEqual(params["as_bool"], True)

    def test_unsupported_result_type_surfaces_as_error(self) -> None:
        specs = ConfigSpecs(
            {
                "samples": ParamSet(ConfigSpecs({"mass": FloatParam()})),
                # An aggregate reference without a reducer yields a list, which
                # is not a supported computed result.
                "bad": ComputedParam(expression="@samples[].mass"),
            }
        )
        computed, errors = specs.compute_values({"samples": [{"mass": 1.0}]})
        self.assertIsNone(computed["bad"])
        self.assertIn("bad", errors)


# test_computed_param
class TestComputedParamMisc(TestCase):
    def test_int_param_without_default_still_works_with_computed_sibling(self) -> None:
        # Regression: adding a ComputedParam should not change normal mandatory checks.
        specs = ConfigSpecs(
            {
                "a": IntParam(),
                "computed": ComputedParam(expression="@a * 2"),
            }
        )
        with self.assertRaises(MissingConfigsException):
            specs.build_config_params({})

    def test_optional_user_field_with_computed(self) -> None:
        specs = ConfigSpecs(
            {
                "a": IntParam(default_value=5),
                "computed": ComputedParam(expression="@a * 2"),
            }
        )
        params = specs.build_config_params({})
        self.assertEqual(params["a"], 5)
        self.assertEqual(params["computed"], 10)

    def test_string_computed(self) -> None:
        specs = ConfigSpecs(
            {
                "first": StrParam(),
                "last": StrParam(),
                "full_name": ComputedParam(
                    expression='concat(@first, " ", @last)'
                ),
            }
        )
        params = specs.build_config_params({"first": "Ada", "last": "Lovelace"})
        self.assertEqual(params["full_name"], "Ada Lovelace")

    def test_bool_computed(self) -> None:
        specs = ConfigSpecs(
            {
                "x": IntParam(),
                "is_positive": ComputedParam(expression="@x > 0"),
            }
        )
        params = specs.build_config_params({"x": 5})
        self.assertTrue(params["is_positive"])
        params = specs.build_config_params({"x": -2})
        self.assertFalse(params["is_positive"])


# test_computed_param
class TestComputedParamInTask(TestCase):
    def setUp(self) -> None:
        ComputedParamTask.received_density = None

    def test_computed_param_resolved_before_run(self) -> None:
        runner = TaskRunner(
            ComputedParamTask,
            params={"mass": 6.0, "volume": 2.0},
            inputs={},
        )
        runner.run()
        self.assertEqual(ComputedParamTask.received_density, 3.0)

    def test_computed_param_recomputes_on_value_change(self) -> None:
        runner = TaskRunner(
            ComputedParamTask,
            params={"mass": 9.0, "volume": 3.0},
            inputs={},
        )
        runner.run()
        self.assertEqual(ComputedParamTask.received_density, 3.0)

        runner = TaskRunner(
            ComputedParamTask,
            params={"mass": 10.0, "volume": 4.0},
            inputs={},
        )
        runner.run()
        self.assertEqual(ComputedParamTask.received_density, 2.5)

    def test_computed_param_error_does_not_block_run(self) -> None:
        # volume=0 → division by zero; per spec, this surfaces as None and the
        # task still runs.
        runner = TaskRunner(
            ComputedParamTask,
            params={"mass": 1.0, "volume": 0.0},
            inputs={},
        )
        runner.run()
        self.assertIsNone(ComputedParamTask.received_density)


# test_computed_param
class TestConfigSpecsConsumerAudit(TestCase):
    """Cross-cutting guard tests for ConfigSpecs consumers.

    Each existing consumer of ConfigSpecs was audited in Phase 0 to make a
    deliberate decision about ComputedParam (accepts_user_input=False) entries:
    skip / compute-then-include / reject. These tests pin those decisions so a
    future regression that re-introduces computed entries into mandatory
    checks, user-input validation, or default-value lookup fails loudly.
    """

    def setUp(self) -> None:
        self.specs = ConfigSpecs(
            {
                "a": FloatParam(),
                "b": FloatParam(),
                "computed": ComputedParam(expression="@a + @b"),
            }
        )

    def test_mandatory_values_are_set_skips_computed(self) -> None:
        # Only `a` and `b` are required; computed never blocks.
        self.assertTrue(self.specs.mandatory_values_are_set({"a": 1.0, "b": 2.0}))
        self.assertFalse(self.specs.mandatory_values_are_set({"a": 1.0}))

    def test_get_and_check_values_does_not_demand_computed_in_input(self) -> None:
        values = self.specs.get_and_check_values({"a": 1.0, "b": 2.0})
        self.assertIn("computed", values)
        self.assertIsNone(values["computed"])  # filled in by compute_values

    def test_get_and_check_values_omits_computed_from_missing_params(self) -> None:
        # `b` missing → MissingConfigs only mentions `b`, not `computed`.
        with self.assertRaises(MissingConfigsException) as ctx:
            self.specs.get_and_check_values({"a": 1.0})
        self.assertNotIn("computed", ctx.exception.missing_params)

    def test_get_default_values_returns_none_for_computed(self) -> None:
        defaults = self.specs.get_default_values()
        self.assertIsNone(defaults["computed"])

    def test_build_config_params_evaluates_computed_entries(self) -> None:
        params = self.specs.build_config_params({"a": 1.0, "b": 2.0})
        self.assertEqual(params["computed"], 3.0)

    def test_existing_param_specs_default_to_accepts_user_input_true(self) -> None:
        spec = IntParam(default_value=1)
        self.assertTrue(spec.accepts_user_input)
