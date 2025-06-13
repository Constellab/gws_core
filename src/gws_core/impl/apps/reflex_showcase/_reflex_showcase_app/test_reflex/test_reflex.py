import asyncio
from typing import List

import reflex as rx
from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

# from gws_core.core.utils.logger import Logger


class MyObject(BaseModel):
    name: str
    value: int


class SecondState(rx.State):
    value: int = 17


class State(rx.State):
    count: int = 0
    list_: List[int] = []

    my_object: MyObject = MyObject(name="Test", value=42)

    def increment(self):
        self.count += 1
        self._refresh_list()
        # Logger.info('Incremented count:' + str(self.count))

    def decrement(self):
        self.count -= 1
        self._refresh_list()
        # print('Decremented count:', self.router.headers.raw_headers)
        # print('Decremented count:', self.router.headers)
        # Logger.info('Decremented count:' + str(self.count))

    def _refresh_list(self):
        if self.count > 0:
            self.list_ = list(range(1, self.count + 1))
        else:
            self.list_ = []

    @rx.var
    async def get_other_value(self) -> int:
        self.is_hydrated
        # Simulate an async operation like an API call
        # return SecondState.value
        # return self.count * 10
        settings = await self.get_state(SecondState)
        return settings.value


def index():
    return rx.box(
        rx.hstack(
            rx.button(
                "Decrement",
                color_scheme="ruby",
                on_click=State.decrement,
            ),
            rx.heading(State.count, font_size="2em"),
            rx.button(
                "Increment",
                color_scheme="grass",
                on_click=State.increment,
            ),
            spacing="4",
        ),
        rx.text(
            f"MyObject: {State.my_object.name} has value {State.my_object.value}",
        ),
        rx.cond(
            State.count > 0,
            rx.foreach(
                State.list_,
                lambda item: rx.text(f"Item {item}"),
            ),
            rx.text("Is negative"),
        ),
        rx.text(
            f"Other value: {State.get_other_value}",
        ),

    )


# Create a FastAPI app with authentication
fastapi_app = FastAPI(title="Secure API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Add a protected route


@fastapi_app.get("/api/protected")
async def protected_route(
    token: str = Depends(oauth2_scheme),
):
    return dict(message="This is a protected endpoint")


# Create a token endpoint
@fastapi_app.post("/token")
async def login(username: str, password: str):
    # In a real app, you would validate credentials
    if username == "user" and password == "password":
        return dict(
            access_token="example_token",
            token_type="bearer",
        )
    return dict(error="Invalid credentials")


app = rx.App(api_transformer=fastapi_app)
app.add_page(index)
