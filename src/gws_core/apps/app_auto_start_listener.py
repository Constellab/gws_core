from gws_core.apps.app_dto import AppStopPolicy
from gws_core.apps.app_gateway_service import AppGatewayService
from gws_core.apps.app_resource import AppResource
from gws_core.core.utils.logger import Logger
from gws_core.lab.system_event import SystemStartedEvent
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.model.event.event_listener_decorator import event_listener
from gws_core.resource.resource_model import ResourceModel
from gws_core.user.current_user_service import AuthenticateUser


@event_listener
class AppAutoStartListener(EventListener):
    """(Cold-)start every MANUAL-stop-policy app when the lab starts.

    An AUTO app is stopped as soon as it has no connection, so it is started on demand by the
    gateway. A MANUAL app is meant to stay alive until explicitly stopped, which means nothing
    would ever bring it back after a lab restart — this listener does.

    Asynchronous on purpose: it runs in the dispatcher's DB-connected worker thread, so spawning
    the app processes never blocks the uvicorn startup, and a failing app only logs an error
    instead of aborting the lab boot.
    """

    def handle(self, event: Event) -> None:
        if not isinstance(event, SystemStartedEvent):
            return
        _start_manual_apps()


def _start_manual_apps() -> None:
    """Start all persisted, non-archived app resources whose stop policy is MANUAL.

    Archived apps are skipped: they are not reachable from the lab anymore, so keeping a process
    alive for them would waste a port and count against MAX_RUNNING_APPS.

    Each app is started independently: one failing app (bad env, port exhaustion, reached
    MAX_RUNNING_APPS) must not prevent the others from starting.

    Runs as the system user: nobody is logged in during the lab boot, and the resource layer
    expects a current user.
    """
    with AuthenticateUser.system_user():
        app_models = ResourceModel.select_by_type_and_sub_types(AppResource).where(
            ResourceModel.is_archived == False  # noqa: E712 (peewee needs ==, not `is`)
        )

        for resource_model in app_models:
            try:
                app_resource = resource_model.get_resource(resource_type=AppResource)
                if not isinstance(app_resource, AppResource):
                    continue
                if app_resource.get_stop_policy() != AppStopPolicy.MANUAL:
                    continue

                AppGatewayService.start_app_and_get_status_token(app_resource)
                Logger.info(
                    f"Auto-started MANUAL app '{app_resource.get_name()}' ({resource_model.id})"
                )
            except Exception as e:
                Logger.error(
                    f"Could not auto-start the MANUAL app {resource_model.id}: {e}", exception=e
                )
