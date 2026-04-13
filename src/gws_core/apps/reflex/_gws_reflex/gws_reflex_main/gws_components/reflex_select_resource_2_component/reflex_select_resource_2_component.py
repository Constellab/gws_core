from typing import Any

import reflex as rx
from gws_reflex_main.reflex_user_auth import ReflexUserAuthInfo
from reflex.vars import Var

from gws_core.core.model.model_dto import BaseModelDTO
from gws_core.resource.resource_front_search_filters import ResourceFrontSearchFilters
from gws_core.resource.resource_model import ResourceModel

from ...reflex_main_state import ReflexMainState

asset_path = rx.asset("reflex_select_resource_2_component.jsx", shared=True)
public_js_path = "$/public/" + asset_path


class SelectResourceInputDTO(BaseModelDTO):
    """DTO matching the DcSelectResourceInput interface.

    :param placeholder: Placeholder text displayed in the input field when empty.
    :type placeholder: str
    :param default_resource: Optional default resource to pre-select.
    :type default_resource: Any | None
    :param default_filters: Optional default filters to apply to the resource search
        (matches Partial<LiResourceSearchFields>).
    :type default_filters: dict | None
    :param disabled_filters: Optional disabled filters flags
        (matches Partial<LiResourceSearchFieldsDisabled>).
    :type disabled_filters: dict | None
    """

    placeholder: str
    default_resource: Any | None = None
    default_filters: dict | None = None
    disabled_filters: dict | None = None


class SelectResource2Component(rx.Component):
    """Select Resource component using dc-select-resource web component.

    This component provides a resource search and selection interface.
    It mirrors the DcSelectResourceComponent Angular component.
    """

    library = public_js_path
    tag = "SelectResource2Component"

    input_data: Var[dict | None]
    """Input data matching the DcSelectResourceInput interface."""

    authentication_info: Var[ReflexUserAuthInfo | None]
    """Authentication info matching the DcAuthenticationInfo interface."""

    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)]
    """Event handler called when a resource is selected. Receives a dict with key
    'resourceId' (str | None) matching DcSelectResourceOutput."""


def select_resource_2_component(
    input_data: SelectResourceInputDTO | Var[dict],
    output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
    **kwargs,
):
    """Create a SelectResource2Component instance.

    This component wraps the dc-select-resource web component and matches the
    DcSelectResourceComponent Angular inputs/outputs:

    - Required input: DcSelectResourceInput
    - Optional input: DcAuthenticationInfo (provided automatically from ReflexMainState)
    - Output event: DcSelectResourceOutput (``{"resourceId": str | None}``)

    :param input_data: Input configuration for the component (required). Can be a
        SelectResourceInputDTO instance or a reflex Var of a dict with matching shape.
    :type input_data: SelectResourceInputDTO | Var[dict]
    :param output_event: Event handler called when the selection changes. Receives a
        dict ``{"resourceId": str | None}``, defaults to None
    :type output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]], optional
    :return: Instance of SelectResource2Component
    :rtype: SelectResource2Component
    """
    if isinstance(input_data, SelectResourceInputDTO):
        input_data_value = input_data.to_json_dict()
    else:
        input_data_value = input_data

    return SelectResource2Component.create(
        input_data=input_data_value,
        authentication_info=ReflexMainState.get_reflex_user_auth_info,
        output_event=output_event,
        **kwargs,
    )


class ReflexResourceSelect:
    """Reflex component to select a resource.

    This component is a wrapper around the GWS resource search component.
    It allows the user to search and select a resource.
    """

    def select_resource(
        self,
        placeholder: str = "Search for resource",
        default_resource: ResourceModel | None = None,
        output_event: rx.EventHandler[rx.event.passthrough_event_spec(dict)] | None = None,
        search_filters: ResourceFrontSearchFilters | None = None,
        **kwargs,
    ) -> rx.Component:
        """Render the resource select component using the configured filters.

        :param placeholder: Placeholder text shown within the component for empty searches,
            defaults to 'Search for resource'
        :type placeholder: str, optional
        :param default_resource: Default resource to show, defaults to None
        :type default_resource: ResourceModel | None, optional
        :param output_event: Event handler called when the selection changes. Receives a
            dict ``{"resourceId": str | None}``, defaults to None
        :type output_event: Optional[rx.EventHandler[rx.event.passthrough_event_spec(dict)]], optional
        :param search_filters: Optional ``ResourceFrontSearchFilters`` instance holding the
            default and disabled filter configuration. When None, no filter is applied,
            defaults to None
        :type search_filters: ResourceFrontSearchFilters | None, optional
        :return: The rendered reflex component
        :rtype: rx.Component
        """
        input_data = SelectResourceInputDTO(
            placeholder=placeholder,
            default_resource=default_resource.to_dto() if default_resource is not None else None,
            default_filters=search_filters.filters if search_filters is not None else None,
            disabled_filters=search_filters.disabled_filters if search_filters is not None else None,
        )

        return select_resource_2_component(
            input_data=input_data,
            output_event=output_event,
            **kwargs,
        )
