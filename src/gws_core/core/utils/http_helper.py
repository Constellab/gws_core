from starlette_context import context


class HTTPHelper:
    @classmethod
    def is_http_context(cls):
        try:
            # -> if not exception -> return True
            context.data["is_http_context"] = True
            return True
        except:
            return False
