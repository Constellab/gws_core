import reflex as rx
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo
from reflex.vars import Var

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.resource.resource_dto import ResourceModelDTO
from gws_core.resource.resource_front_search_filters import ResourceFrontSearchFilters

from ...reflex_main_state import ReflexMainState

asset_path = rx.asset("reflex_select_resource_2_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path


class SelectResourceInputDTO(BaseModelDTO):
    """DTO matching the DcSelectResourceInput interface.

    :param placeholder: Placeholder text displayed in the input field when empty.
    :type placeholder: str
    :param default_resource: Optional default resource to pre-select.
    :type default_resource: ResourceModelDTO | None
    :param default_filters: Optional default filters to apply to the resource search
        (matches Partial<LiResourceSearchFields>).
    :type default_filters: dict | None
    :param disabled_filters: Optional disabled filters flags
        (matches Partial<LiResourceSearchFieldsDisabled>).
    :type disabled_filters: dict | None
    """

    placeholder: str
    default_resource: ResourceModelDTO | None = None
    default_filters: dict | None = None
    disabled_filters: dict | None = None


class SelectResource2Component(rx.Component):
    """Select Resource component using dc-select-resource web component.

    This component provides a resource search and selection interface.
    It mirrors the DcSelectResourceComponent Angular component.
    """

    library = public_js_path
    tag = "SelectResource2Component"

    input_data: Var[SelectResourceInputDTO | None]
    """Input data matching the DcSelectResourceInput interface."""

    authentication_info: Var[ReflexUserAuthInfo | None]
    """Authentication info matching the DcAuthenticationInfo interface."""

    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    """Event handler called when a resource is selected. Receives a dict with key
    'resourceId' (str | None) matching DcSelectResourceOutput."""


def select_resource_2_component(
    input_data: SelectResourceInputDTO | Var[SelectResourceInputDTO],
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
    **kwargs,
):
    """Create a SelectResource2Component instance.

    This component wraps the dc-select-resource web component and matches the
    DcSelectResourceComponent Angular inputs/outputs:

    - Required input: DcSelectResourceInput
    - Optional input: DcAuthenticationInfo (provided automatically from ReflexMainState)
    - Output event: DcSelectResourceOutput (``{"resourceId": str | None}``)

    :param input_data: Input configuration for the component (required). Either a
        ``SelectResourceInputDTO`` instance or a reflex ``Var`` of one (returned by an
        ``@rx.var`` that depends on reactive state).
    :type input_data: SelectResourceInputDTO | Var[SelectResourceInputDTO]
    :param output_event: Event handler called when the selection changes. Receives a
        dict ``{"resourceId": str | None}``, defaults to None
    :type output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]], optional
    :return: Instance of SelectResource2Component
    :rtype: SelectResource2Component
    """
    return SelectResource2Component.create(
        input_data=input_data,
        authentication_info=ReflexMainState.get_reflex_user_auth_info,
        output_event=output_event,
        **kwargs,
    )


class SelectResourceInput:
    """Python-side configuration for the resource select component.

    Mirrors :class:`SelectResourceInputDTO` but accepts a
    :class:`ResourceFrontSearchFilters` instance instead of the raw filter
    dictionaries. Use :meth:`to_dto` to produce the DTO consumed by the
    underlying component.

    :ivar placeholder: Placeholder text displayed in the input field when empty.
    :vartype placeholder: str
    :ivar default_resource: Optional default resource to pre-select.
    :vartype default_resource: ResourceModelDTO | None
    :ivar search_filters: Optional ``ResourceFrontSearchFilters`` instance holding
        the default and disabled filter configuration.
    :vartype search_filters: ResourceFrontSearchFilters | None
    """

    placeholder: str
    default_resource: ResourceModelDTO | None
    search_filters: ResourceFrontSearchFilters | None

    def __init__(
        self,
        placeholder: str = "Search for resource",
        default_resource: ResourceModelDTO | None = None,
        search_filters: ResourceFrontSearchFilters | None = None,
    ) -> None:
        self.placeholder = placeholder
        self.default_resource = default_resource
        self.search_filters = search_filters

    def to_dto(self) -> SelectResourceInputDTO:
        """Convert this input into the DTO consumed by the component."""
        return SelectResourceInputDTO(
            placeholder=self.placeholder,
            default_resource=self.default_resource,
            default_filters=self.search_filters.filters if self.search_filters is not None else None,
            disabled_filters=self.search_filters.disabled_filters
            if self.search_filters is not None
            else None,
        )
