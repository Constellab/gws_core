

from abc import abstractmethod
from typing import Generic, List, Type, TypeVar

from gws_core.core.model.model import Model
from gws_core.core.utils.logger import Logger
from gws_core.model.event.event import Event
from gws_core.model.event.event_listener import EventListener
from gws_core.user.user_service import UserService

from .user import User

# Type variable for custom user models that must extend Model
TCustomUser = TypeVar('TCustomUser', bound=Model)


class UserSyncService(EventListener, Generic[TCustomUser]):
    """
    Abstract base class for synchronizing users from gws_core database to custom databases.

    This service extends EventListener to automatically sync users when user events occur.
    It provides both synchronization logic and event handling in a single all-in-one class.

    IMPORTANT: When creating your implementation, you must decorate it with @event_listener
    to register it with the event system.

    Type Parameters:
        TCustomUser: The type of the custom user model in the target database (must extend Model)

    Example:
        from gws_core import User as GwsCoreUser
        from gws_core import event_listener

        @event_listener
        class ProjectUserSyncService(UserSyncService[ProjectUser]):
            def get_user_type(self) -> Type[ProjectUser]:
                return ProjectUser

            def update_custom_user_attributes(self, custom_user: ProjectUser, gws_core_user: User) -> ProjectUser:
                # Only update attributes, do not save
                custom_user.email = gws_core_user.email
                custom_user.first_name = gws_core_user.first_name
                # ... update other fields
                return custom_user
    """

    def sync_all_users(self, gws_core_users: List[User]) -> None:
        """
        Synchronize multiple users from gws_core to the custom database.

        This method iterates through all provided gws_core users and syncs each one.
        Errors are logged but don't stop the synchronization process.

        :param gws_core_users: List of User objects from gws_core to synchronize
        :type gws_core_users: List[User]
        """
        Logger.debug(f"Starting synchronization of {len(gws_core_users)} users")

        errors = []
        synced_count = 0

        for gws_core_user in gws_core_users:
            try:
                self.sync_user(gws_core_user)
                synced_count += 1
            except Exception as e:
                error_msg = f"Error syncing user {gws_core_user.email} (ID: {gws_core_user.id}): {str(e)}"
                Logger.error(error_msg)
                errors.append(error_msg)

        Logger.debug(
            f"Synchronization completed: "
            f"{synced_count} succeeded, {len(errors)} failed"
        )

        if errors:
            Logger.warning(
                f"Encountered {len(errors)} errors during synchronization"
            )

    def sync_user(self, gws_core_user: User) -> TCustomUser:
        """
        Synchronize a single user from gws_core to the custom database.

        This method checks if the user exists in the custom database:
        - If the user exists, it updates the existing record
        - If the user doesn't exist, it creates a new record

        :param gws_core_user: The User object from gws_core to synchronize
        :type gws_core_user: User
        :return: The synchronized custom user object
        :rtype: TCustomUser
        """
        user_type = self.get_user_type()
        custom_user = user_type.get_by_id(gws_core_user.id)

        force_insert = False
        if custom_user is None:
            # Build new user object (not yet saved)
            custom_user = user_type(id=gws_core_user.id)
            force_insert = True

        # Update the custom user object with gws_core user data (not yet saved)
        custom_user = self.update_custom_user_attributes(custom_user, gws_core_user)

        # Save and return
        return custom_user.save(force_insert=force_insert)

    @abstractmethod
    def get_user_type(self) -> Type[TCustomUser]:
        """
        Return the custom user model class type.

        This method should return the class (not an instance) of your custom user model.
        The returned class must extend gws_core.core.model.model.Model.

        :return: The custom user model class
        :rtype: Type[TCustomUser]

        Example:
            def get_user_type(self) -> Type[ProjectUser]:
                return ProjectUser
        """

    @abstractmethod
    def update_custom_user_attributes(self, custom_user: TCustomUser, gws_core_user: User) -> TCustomUser:
        """
        Update the attributes of a custom user object with data from a gws_core user.

        This method should copy all relevant fields from the gws_core user to the
        custom user object and return the updated object.

        IMPORTANT: This method should only update the object attributes.
        Do NOT save it to the database. The object will be saved by the sync_user method.

        :param custom_user: The custom user object to update
        :type custom_user: TCustomUser
        :param gws_core_user: The source User object from gws_core
        :type gws_core_user: User
        :return: The updated custom user object (NOT saved to database)
        :rtype: TCustomUser

        Example:
            def update_custom_user_attributes(self, custom_user: ProjectUser, gws_core_user: User) -> ProjectUser:
                # Only update attributes, do not save
                custom_user.email = gws_core_user.email
                custom_user.first_name = gws_core_user.first_name
                custom_user.last_name = gws_core_user.last_name
                return custom_user
        """

    def get_custom_user_by_id(self, user_id: str) -> TCustomUser | None:
        """
        Retrieve a custom user by ID from the custom database.

        This method uses the get_user_type() to retrieve the user model class
        and calls get_by_id() on it.

        :param user_id: The ID of the user to retrieve
        :type user_id: str
        :return: The custom user object if found, None otherwise
        :rtype: TCustomUser | None
        """
        user_type = self.get_user_type()
        return user_type.get_by_id(user_id)

    def get_all_custom_users(self) -> List[TCustomUser]:
        """
        Retrieve all custom users from the custom database.

        This method uses the get_user_type() to retrieve the user model class
        and performs a select() query to get all users.

        :return: List of all custom user objects
        :rtype: List[TCustomUser]
        """
        user_type = self.get_user_type()
        return list(user_type.select())

    def get_or_import_user(self, user_id: str, gws_core_user: User | None = None) -> TCustomUser | None:
        """
        Get a custom user by ID, or import from gws_core if not found.

        This is a convenience method for lazy synchronization. It first tries to
        retrieve the user from the custom database. If not found, it synchronizes
        the user from gws_core (if provided).

        :param user_id: The ID of the user to retrieve
        :type user_id: str
        :param gws_core_user: Optional gws_core user to sync if not found
        :type gws_core_user: User | None
        :return: The custom user object if found or synchronized, None otherwise
        :rtype: TCustomUser | None
        """
        custom_user = self.get_custom_user_by_id(user_id)

        if custom_user is None and gws_core_user is not None:
            custom_user = self.sync_user(gws_core_user)

        return custom_user

    def handle(self, event: Event) -> None:
        """
        Handle incoming events from the gws_core event system.

        This method automatically syncs users when relevant events occur:
        - system.started: Syncs all users from gws_core when the system starts
        - user.created: Syncs the newly created user
        - user.updated: Syncs the updated user
        - user.activated: Syncs the user when activated/deactivated

        Override this method if you need custom event handling logic.

        :param event: The event to handle
        :type event: Event
        """
        # Sync all users when system starts
        if event.type == 'system' and event.action == 'started':
            gws_core_users = UserService.get_all_users()
            self.sync_all_users(gws_core_users)

        # Sync individual user on user events
        elif event.type == 'user' and event.action in ('created', 'updated', 'activated'):
            self.sync_user(event.data)
