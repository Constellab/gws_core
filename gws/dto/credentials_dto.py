from pydantic import BaseModel

class CredentialsDTO(BaseModel):
    email: str
    password: str
    