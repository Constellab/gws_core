import jwt

# Runs in an isolated conda/mamba env without gws_core, and the test asserts on this
# script's stdout, so print is the contract here and the GWS Logger is unavailable.
print(jwt.encode({"some": "payload"}, "secret", algorithm="HS256"))  # noqa: T201
