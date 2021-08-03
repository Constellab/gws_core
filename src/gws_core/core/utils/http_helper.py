# LICENSE
# This software is the exclusive property of Gencovery SAS.
# The use and distribution of this software is prohibited without the prior consent of Gencovery SAS.
# About us: https://gencovery.com

from starlette_context import context


class HTTPHelper:

    @classmethod
    def is_http_context(cls):
        try:
            # -> if not exception -> return True
            context.data["is_http_context"] = True
            return True
        except Exception as _:
            return False
