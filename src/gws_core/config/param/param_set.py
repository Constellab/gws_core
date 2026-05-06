import uuid
from typing import Any

from gws_core.config.config_change_dto import ConfigChangeAction, ConfigChangeEntry
from gws_core.config.config_specs import ConfigSpecs
from gws_core.config.param.param_spec_decorator import ParamSpecCategory, param_spec_decorator
from gws_core.core.utils.logger import Logger

from ...core.classes.validator import DictValidator, ListValidator
from .param_spec import ParamSpec
from .param_types import ParamSpecDTO, ParamSpecType, ParamSpecVisibilty


@param_spec_decorator(label="Param set", type_=ParamSpecCategory.NESTED)
class ParamSet(ParamSpec):
    """ParamSet. Use to define a group of parameters that can be added multiple times. This will
    provid a list of dictionary as values : List[Dict[str, Any]]

    """

    param_set: ConfigSpecs | None = None
    max_number_of_occurrences: int

    def __init__(
        self,
        param_set: ConfigSpecs | None = None,
        optional: bool = False,
        visibility: ParamSpecVisibilty = "public",
        human_name: str | None = None,
        short_description: str | None = None,
        max_number_of_occurrences: int = -1,
    ):
        """
        :param optional: It true, the param_set can have 0 occurence, the value will then be an empty array [].
        :type optional: Optional[str]
        :param visibility: Visibility of the param. It override all child spec visibility. see doc on type ParamSpecVisibilty for more info
        :type visibility: ParamSpecVisibilty
        :param human_name: Human readable name of the param, showed in the interface
        :type human_name: Optional[str]
        :param short_description: Description of the param, showed in the interface
        :type short_description: Optional[str]
        :param max_number_of_occurrences: Nb max of occurence of values the params. If negative, there is no limit.
        :type max_number_of_occurrences: Optional[str]
        """

        self.max_number_of_occurrences = max_number_of_occurrences

        if param_set is None:
            param_set = ConfigSpecs()

        if isinstance(param_set, dict):
            Logger.warning("ParamSet: param_set should be a ConfigSpecs object, not a dict. ")
            param_set = ConfigSpecs(param_set)

        self.param_set = param_set
        super().__init__(
            default_value=[] if optional else None,
            optional=optional,
            visibility=visibility,
            human_name=human_name,
            short_description=short_description,
        )

    def get_default_value(self) -> list:
        if self.optional:
            return []

        # if this is not optional, return an array of 1 element with the
        # default value of each param_spec
        return [self.param_set.get_default_values()]

    def validate(self, value: list[dict[str, Any]]) -> Any:
        """Validate a ParamSet value (list of row dicts) and reconcile per-row
        identity.

        Each row carries a reserved ``ConfigSpecs.ITEM_ID_KEY`` (``__item_id``)
        — a UUID v4 stable across saves. Clients should generate it themselves
        for new rows; the server fills it in if missing. Duplicate ids within
        the same ParamSet are rejected.

        The id is stripped before delegating to the inner
        ``ConfigSpecs.get_and_check_values`` (which would otherwise reject the
        unknown reserved key) and re-attached on the validated dict.
        """
        if value is None:
            return []
        list_validator = ListValidator(max_number_of_occurrences=self.max_number_of_occurrences)
        dict_validator = DictValidator()

        # global validation of the list
        list_: list[dict[str, Any]] = list_validator.validate(value)

        result_list = []
        seen_ids: set[str] = set()
        for dict_ in list_:
            # Valid on dict of param set
            valid_dict = dict_validator.validate(dict_)

            item_id = valid_dict.get(ConfigSpecs.ITEM_ID_KEY) or str(uuid.uuid4())
            if item_id in seen_ids:
                raise ValueError(f"Duplicate {ConfigSpecs.ITEM_ID_KEY} '{item_id}' in ParamSet")
            seen_ids.add(item_id)

            # get_and_check_values iterates self.specs only, so __item_id is
            # silently ignored by it; no need to strip the input.
            validated_item = self.param_set.get_and_check_values(valid_dict)
            validated_item[ConfigSpecs.ITEM_ID_KEY] = item_id
            result_list.append(validated_item)

        return result_list

    @staticmethod
    def diff_values(
        key: str,
        old_val: Any,
        new_val: Any,
    ) -> list:
        """Diff two ParamSet values (lists of row dicts) by ``__item_id``.

        Produces:
        - PARAMSET_ITEM_REMOVED for ids only in old (path: ``key[item_id=<uuid>]``).
        - PARAMSET_ITEM_ADDED for ids only in new.
        - One FIELD_CREATED / FIELD_UPDATED / FIELD_DELETED per inner field change
          for ids present on both sides (path: ``key[item_id=<uuid>].<field>``).

        Reorder = same set of ids on both sides with no inner change → no entries.

        ``__item_id`` is stripped from old_value / new_value payloads on
        ITEM_ADDED / ITEM_REMOVED entries — the path already carries the id.
        """
        old_rows: list[dict[str, Any]] = old_val if isinstance(old_val, list) else []
        new_rows: list[dict[str, Any]] = new_val if isinstance(new_val, list) else []

        old_by_id = {
            row.get(ConfigSpecs.ITEM_ID_KEY): row
            for row in old_rows
            if isinstance(row, dict) and row.get(ConfigSpecs.ITEM_ID_KEY)
        }
        new_by_id = {
            row.get(ConfigSpecs.ITEM_ID_KEY): row
            for row in new_rows
            if isinstance(row, dict) and row.get(ConfigSpecs.ITEM_ID_KEY)
        }

        changes: list = []

        for item_id in sorted(set(old_by_id) - set(new_by_id)):
            changes.append(
                ConfigChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=ConfigChangeAction.PARAMSET_ITEM_REMOVED,
                    old_value=ParamSet._strip_id(old_by_id[item_id]),
                    new_value=None,
                )
            )
        for item_id in sorted(set(new_by_id) - set(old_by_id)):
            changes.append(
                ConfigChangeEntry(
                    field_path=f"{key}[item_id={item_id}]",
                    action=ConfigChangeAction.PARAMSET_ITEM_ADDED,
                    old_value=None,
                    new_value=ParamSet._strip_id(new_by_id[item_id]),
                )
            )

        for item_id in sorted(set(old_by_id) & set(new_by_id)):
            old_row = old_by_id[item_id]
            new_row = new_by_id[item_id]
            inner_keys = (set(old_row.keys()) | set(new_row.keys())) - {ConfigSpecs.ITEM_ID_KEY}
            for inner_key in sorted(inner_keys):
                in_old = inner_key in old_row
                in_new = inner_key in new_row
                old_inner = old_row.get(inner_key)
                new_inner = new_row.get(inner_key)
                inner_path = f"{key}[item_id={item_id}].{inner_key}"
                changes.extend(
                    ConfigSpecs.diff_scalar(inner_path, old_inner, new_inner, in_old, in_new)
                )

        return changes

    @staticmethod
    def _strip_id(row: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in row.items() if k != ConfigSpecs.ITEM_ID_KEY}

    def to_dto(self) -> ParamSpecDTO:
        json_: ParamSpecDTO = super().to_dto()

        # convert the additional info to json
        json_.additional_info = {
            "max_number_of_occurrences": self.max_number_of_occurrences,
            "param_set": self.param_set.to_dto(),
        }

        return json_

    @classmethod
    def get_param_spec_type(cls) -> ParamSpecType:
        return ParamSpecType.PARAM_SET

    @classmethod
    def load_from_dto(cls, spec_dto: ParamSpecDTO, validate: bool = False) -> "ParamSet":
        from .param_spec_helper import ParamSpecHelper

        param_set: ParamSet = super().load_from_dto(spec_dto, validate=validate)

        # load info from additional info
        param_set.max_number_of_occurrences = spec_dto.additional_info.get(
            "max_number_of_occurrences"
        )

        specs = ConfigSpecs()

        for key, param in spec_dto.additional_info.get("param_set").items():
            specs.add_spec(
                key, ParamSpecHelper.create_param_spec_from_json(param, validate=validate)
            )

        param_set.param_set = specs

        return param_set

    @classmethod
    def get_default_value_param_spec(cls) -> "ParamSet":
        return ParamSet()

    @classmethod
    def get_additional_infos(cls) -> dict[str, ParamSpecDTO] | None:
        return None
