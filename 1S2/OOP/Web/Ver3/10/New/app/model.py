from pydantic import BaseModel, Field, EmailStr

class PostModel(BaseModel):
    id : int = Field(default=None, alias="_id")
    title : str = Field(default=None, alias="title")
    content : str = Field(default=None, alias="content")
    class Config:
        json_schema_extra = {
            "example": {
                "title": "Title of the post",
                "content": "Content of the post"
            }
        }

class RegisterModel(BaseModel):
    name : str = Field(default=None, alias="name")
    email : EmailStr = Field(default=None, alias="email")
    password : str = Field(default=None, alias="password")
    class Config:
        the_shcema = {
            "example": {
                "name": "tur",
                "email": 'gg@gg.com',
                "password": "123"
            }
        }

class LoginModel(BaseModel):
    email : EmailStr = Field(default=None, alias="email")
    password : str = Field(default=None, alias="password")
    class Config:
        the_shcema = {
            "example": {
                "email": 'gg@gg.com',
                'password': "123"
            }
        }