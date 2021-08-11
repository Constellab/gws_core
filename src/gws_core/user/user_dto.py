from typing import TypedDict

from pydantic import BaseModel


class UserData(BaseModel):
    uri: str
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    group: str = "user"
    is_active: bool
    is_admin: bool
    is_http_authenticated: bool = False
    is_console_authenticated: bool = False


class UserDataDict(TypedDict):
    uri: str
    email: str
    first_name: str
    last_name: str
    group: str
    is_active: bool
    is_admin: bool
    is_http_authenticated: bool
    is_console_authenticated: bool
