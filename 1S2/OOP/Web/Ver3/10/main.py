import uvicorn
from fastapi import FastAPI, Body, Depends, HTTPException
from app.model import PostModel , RegisterModel, LoginModel
from app.auth import signJWT
from app.check_auth import jwtBearer
from internals.controller import Controller

app = FastAPI()

controller = Controller()

@app.post("/register")
def register(user: RegisterModel = Body(default=None)):
    controller.create_user(user)
    return signJWT(user.email)

def check_user(data: LoginModel):
    for user in users:
        if user.email == data.email and user.password == data.password:
            return True
    return False

@app.post('/login')
def login(user: LoginModel = Body(...)):
    if check_user(user):
        return signJWT(user.email)
    return {"error": "Invalid credentials"}

