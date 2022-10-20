import jwt

encoded_jwt = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
# expected value encoded_jwt = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzb21lIjoicGF5bG9hZCJ9.4twFt5NiznN84AWoo1d7KO1T_yoc0Z6XOpOVswacPZg
print(encoded_jwt, end="")
