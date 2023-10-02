import jwt

print(jwt.encode({"some": "payload"}, "secret", algorithm="HS256"))
