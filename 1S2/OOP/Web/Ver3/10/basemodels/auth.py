from pydantic import BaseModel

class RegisterModel(BaseModel):
    username : str
    password : str

class tokenModel(BaseModel):
    access_token : str
    token_type : str