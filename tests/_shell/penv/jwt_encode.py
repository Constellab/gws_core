import jwt

encoded_jwt = jwt.encode({"some": "payload"}, "secret", algorithm="HS256")
# expected value encoded_jwt = eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzb21lIjoicGF5bG9hZCJ9.Joh1R2dYzkRvDkqv3sygm5YyK8Gi4ShZqbhK2gxcs2U
print(encoded_jwt, end="")
