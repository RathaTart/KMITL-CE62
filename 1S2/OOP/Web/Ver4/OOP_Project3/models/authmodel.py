from pydantic import BaseModel

class RegisterModel(BaseModel):
    name : str
    role : str = 'customer'
    password : str
    class Config:
        the_shcema = {
            "example": {
                "name": "tur",
                "password": "123"
            }
        }

class LoginModel(BaseModel):
    name : str
    password : str
    class Config:
        the_shcema = {
            "example": {
                "name": 'tur',
                'password': "123"
            }
        }