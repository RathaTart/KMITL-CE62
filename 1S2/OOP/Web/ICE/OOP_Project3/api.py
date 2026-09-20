from coupon import Coupon
from basket import Basket
from pizza import Pizza, Pizza_item
from controller import Controller
from pydantic import BaseModel 

from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import os
import uvicorn

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import json

import jwt
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Optional
from datetime import datetime, timedelta

app = FastAPI()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")

# Dummy controller and other imports for demonstration
from controller import Controller
controller = Controller()

# origins = [
#     "http://127.0.0.1:5500/",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["GET", "POST"],  # Adjust based on the methods your API supports
#     allow_headers=["*"],
# )

@app.get('/index/', response_class=HTMLResponse)
def index(request: Request):
    context = {'request': request}
    return templates.TemplateResponse("index.html", context)

static_directory = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_directory, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_directory), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials = True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

controller = Controller()
controller.add_user('tur', "001", "customer", "123")
controller.add_user('tart', "002", "customer", "234")
controller.add_user('ice', "003", "shop", "456")
controller.add_user('tee', "004", "shop", "567")

Turacc = controller.search_customer_account_by_user_id("001")

shop1 = controller.add_shop(101)
shop2 = controller.add_shop(102)
# # Adding stock items to shop 1
# controller.add_stock_to_shop(101, [("A", 1), ("B", 2), ("C", 5)])
# # Adding stock items to shop 2
# controller.add_stock_to_shop(102, [("C", 3), ("D", 2), ("E", 4)])

controller.add_pizza('pepperoni', 10)
controller.add_pizza('margherita', 8)
controller.add_pizza('hawaiian', 12)
controller.add_pizza('A', 5)
# controller.add_drink('coke', 15)

Turacc.basket.add_pizza(controller.create_pizza_item("pepperoni", "L", 2))
Turacc.basket.add_pizza(controller.create_pizza_item("pepperoni", "L", 2))
Turacc.basket.add_pizza(controller.create_pizza_item("margherita", "S", 3))
Turacc.basket.add_pizza(controller.create_pizza_item("margherita", "M", 2))
# Turacc.basket.add_drink(controller.create_drink_item("coke", "M", 3))

controller.add_coupon(Coupon("ABC123", 10, "2024-12-31"))
controller.add_coupon(Coupon("DEF456", 20, "2025-02-28"))
controller.add_coupon(Coupon("GHI789", 30, "2022-12-31"))

controller.add_coupon_to_account("001", "ABC123")
controller.add_coupon_to_account("001", "DEF456")

controller.write_review("001", "good and tasty")

SECRET_KEY = "secret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 120

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login/")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

class loginDTO(BaseModel):
    username: str
    password: str


@app.post('/basket/{user_id}/add_drink', tags=["Basket"])
def add_drink_to_basket(user_id: str, name: str, size: str, quantity: int) -> dict:
    account = controller.search_account_by_user_id(user_id)
    if account:
        if not account.basket:
            account.add_basket(Basket())
        account.basket.add_drink(controller.create_drink_item(name, size, quantity))
        return {"message": "Drink added to basket"}
    else:
        return {"message": "User not found"}

@app.post('/login/')
async def login(user:loginDTO) -> dict:
    account = controller.login(user.username, user.password)
    # if account:
    #     return {"message": f"Login successful for user {account.user.name}"}
    # else:
    #     return {"message": "Login failed"}
    if not account:
        return "login failed" #HTTPException(
        #     status_code=status.HTTP_401_UNAUTHORIZED,
        #     detail="Incorrect username or password",
        #     headers={"WWW-Authenticate": "Bearer"},
        # )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": account.user.id}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get('/coupon', tags=["Coupon"])
def show_coupon():
    coupon_list = controller.show_coupon_available()
    return {"coupon_list": coupon_list}

@app.post('/coupon/{user_id}', tags=["Coupon"])
def add_coupon_to_account(user_id: str, coupon_code: str):
    account = controller.search_customer_account_by_user_id(user_id)
    
    if account:
        if controller.add_coupon_to_account(user_id, coupon_code):
            return {"message": "Coupon added to account"}
        else:
            return {"message": "Coupon not found"}
    else:
        return {"message": "User not found"}


@app.get('/{user_id}/coupon', tags=["Coupon"])  
def show_coupon_of_account(user_id: str):
    coupon_list = []
    account = controller.search_customer_account_by_user_id(user_id)
    if account:
        for coupon in account.coupon_list:
            if coupon.is_valid:
                coupon_list.append(coupon)
        return {"coupon_list": coupon_list}
    else:
        return {"message": "User not found"}

@app.post('/payment', tags=["Payment"])
def process_payment(user_id: str, total_price: int, payment_method: str) -> dict:
    user = controller.search_user_by_id(user_id)
    if user:
        # Here you would implement the actual payment processing logic
        # For demonstration purposes, let's assume the payment is successful
        return {"message": f"Payment of {total_price} units processed successfully for user {user_id} via {payment_method}"}
    else:
        return {"message": "User not found"}

@app.post('/user', tags=["User"])
def create_user(name: str, id: str):
    controller.add_user(name, id)
    return {"message": "user created"}

@app.post ('/user/{user_id}', tags=["User"])
def search_user_by_id(user_id: str):
    user = controller.search_user_by_id(user_id)
    if user:
        return {"name": user.name, "id": user.id, "role": user.role}
    else:
        return {"message": "user not found"}

@app.post ('/user/{user_name}', tags=["User"])
def serach_user_by_name(user_name: str):
    user = controller.search_user_by_name(user_name)
    if user:
        return {"name": user.name, "id": user.id, "role": user.role}
    else:
        return {"message": "user not found"}

@app.get ('/user', tags=["User"])
def show_user_list():
    user_list = controller.show_user_list()
    user_list_response = [{"name": user.name, "id": user.id, "role": user.role} for user in user_list]
    return {"user_list": user_list_response}

@app.get('/account', tags=["Show Account List"])
def show_account_list():
    account_list = controller.show_account_list()
    account_list_response = [{"user_id": account.user.id, "role": account.user.role, "password": account.password} for account in account_list]
    return {"account_list": account_list_response}

class PizzaCustomModel(BaseModel):
    face: str
    size: str
    quantity: str

@app.post('/basket/{user_id}', tags=["Basket"])
def add_pizza_to_basket(body: PizzaCustomModel, req: Request) -> dict:
    try:
        payload = jwt.decode(req.headers['authentication'], SECRET_KEY, algorithms=[ALGORITHM])
        userId = payload.get("sub")
        if userId is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        account = controller.search_customer_account_by_user_id(userId)
        controller.add_pizza(body.face, body.size, body.quantity, account)
        if account:
            if account.basket:
                pizza_list = [pizza_item for pizza_item in account.basket.pizza_list]
                return {"pizza_list": pizza_list}
            else:
                return {"message": "Basket not found"}
        else:
            return {"message": "User not found"}        
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    


@app.get('/basket/', tags=["Basket"])
def get_basket(req: Request):
    try:
        payload = jwt.decode(req.headers['authentication'], SECRET_KEY, algorithms=[ALGORITHM])
        userId = payload.get("sub")
        if userId is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        account = controller.search_customer_account_by_user_id(userId)
        if account:
            if account.basket:
                pizza_list = [pizza_item for pizza_item in account.basket.pizza_list]
                return {"pizza_list": pizza_list}
            else:
                return {"message": "Basket not found"}
        else:
            return {"message": "User not found"}        

    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    

@app.get('/shop', tags=["Search Shop List"])
def get_shop():
    shop_info = []
    for shop in controller.shop_list:
        shop_info.append({"shop_id_branch": shop.shop_id_branch})
    return {"Shops list": shop_info}

# @app.post('/shop', tags=["Check Shop Stock"])
# def check_shop_stock(shop_id_branch: int):
#     stock = controller.check_stock(shop_id_branch)
#     if stock:
#         return {"shop_id_branch": shop_id_branch, "stock": stock}
#     else:
#         return {"message": "shop not found"}

@app.get('/shop_stock')
async def check_shop_stock(shop_id_branch: int):
    if shop_id_branch <= 0:
        return {"message": "Invalid shop ID"}
    stock = controller.check_stock(shop_id_branch)
    if stock:
        return {"shop_id_brance": shop_id_branch, "stock": stock}
    else:
        return {"message": "shop not found"}

@app.post('/add_review', tags=["Review"])
def add_review(review: str, req: Request):
    try:
        payload = jwt.decode(req.headers['authentication'], SECRET_KEY, algorithms=[ALGORITHM])
        userId = payload.get("sub")
        if userId is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        controller.write_review(userId, review)
        return {"message": f"Review added for user {userId}"}
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.get('/review', tags=["Review"])

def see_all_review():
    reviews = controller.get_all_review()
    if reviews:
        return {"reviews": reviews}
    else:
        return {"message": "No reviews found"}


# """