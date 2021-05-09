
from gws.logger import Error
from gws.model import User


class UserService:

    @classmethod
    def create_user(cls, data: dict):
        group = data.get('group', 'user')
        if group == "sysuser":
            raise Error("Central", "create_user", "Cannot create sysuser")

        q = User.get_by_uri(data['uri'])
        if not q:
            user = User(
                uri=data['uri'],
                email=data['email'],
                group=group,
                is_active=data.get('is_active', True),
                data={
                    "first_name": data['first_name'],
                    "last_name": data['last_name'],
                }
            )
            if user.save():
                return User.get_by_uri(user.uri)
            else:
                raise Error("Central", "create_user",
                            "Cannot create the user")
        else:
            raise Error("Central", "create_user",
                        "The user already exists")

    @classmethod
    def get_user_status(cls, uri):
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "get_user_status", "User not found")
        else:
            return {
                "uri": user.uri,
                "group": user.group,
                "console_token": user.console_token,
                "is_active": user.is_active,
                "is_http_authenticated": user.is_http_authenticated,
                "is_console_authenticated": user.is_console_authenticated
            }

    @classmethod
    def set_user_status(cls, uri, data):
        user = User.get_by_uri(uri)
        if user is None:
            raise Error("Central", "set_user_status", "User not found")
        else:
            if not data.get("is_active") is None:
                user.is_active = data.get("is_active")

            if data.get("group"):
                user.group = data.get("group")

            if user.save():
                return cls.get_user_status(user.uri)
            else:
                raise Error("Central", "set_user_status",
                            "Cannot save the user")

    @classmethod
    def activate_user(cls, uri):
        return cls.set_user_status(uri, {"is_active": True})

    @classmethod
    def deactivate_user(cls, uri):
        return cls.set_user_status(uri, {"is_active": False})

    @classmethod
    def get_all_users(cls):
        return list(User.select())

    @classmethod
    def get_user_by_uri(cls, uri):
        return User.get_by_uri(uri)
