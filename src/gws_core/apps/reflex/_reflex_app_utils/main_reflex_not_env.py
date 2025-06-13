import os
from typing import List

import reflex as rx

from gws_core.apps.reflex._reflex_app_utils.main_reflex import \
    ReflexAuthenticationState
from gws_core.core.utils.logger import Logger
from gws_core.resource.resource import Resource
from gws_core.resource.resource_model import ResourceModel


class ReflexAuthenticationStateNotEnv(ReflexAuthenticationState):

    resources: List[Resource] = None

    def on_load(self):
        super().on_load()
        self.resources = self.get_resources('Load')
        Logger.info(
            f"ReflexAuthenticationStateNotEnv.on_load: resources loaded: {len(self.resources)}"
        )

    def get_resources(self, mode: str) -> List[Resource]:
        """Return the resources of the app."""
        Logger.info(
            f"ReflexAuthenticationStateNotEnv.get_resources: is_initialized={self.is_initialized} mode={mode}"
        )
        # if not self.is_initialized:
        #     return []
        sources_ = []
        app_config = self._load_app_config()
        for source_path in app_config['source_ids']:
            resource_model = ResourceModel.get_by_id_and_check(source_path)
            sources_.append(resource_model.get_resource())
        return sources_
