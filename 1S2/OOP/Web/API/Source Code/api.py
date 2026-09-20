from coupon import Coupon
from basket import Basket
from pizza import Pizza, Pizza_item
from controller import Controller

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
import uvicorn

app = FastAPI()
static_directory = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_directory, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_directory), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[""],
)

controller = Controller()
controller.add_user('tur', "001", "customer", "123")
controller.add_user('tart', "002", "customer", "234")
controller.add_user('ice', "003", "shop", "456")
controller.add_user('tee', "004", "shop", "567")

Turacc = controller.search_customer_account_by_user_id("001")

shop1 = controller.add_shop(101)
shop2 = controller.add_shop(102)
# Adding stock items to shop 1
controller.add_stock_to_shop(101, [("A", 1), ("B", 2), ("C", 5)])
# Adding stock items to shop 2
controller.add_stock_to_shop(102, [("C", 3), ("D", 2), ("E", 4)])


controller.add_pizza('pepperoni', 10)
controller.add_pizza('margherita', 8)
controller.add_pizza('hawaiian', 12)
controller.add_pizza('A', 5)

Turacc.basket.add_pizza(controller.create_pizza_item("pepperoni", "L", 2))
Turacc.basket.add_pizza(controller.create_pizza_item("pepperoni", "L", 2))


controller.add_coupon(Coupon("ABC123", 10, "2024-12-31"))
controller.add_coupon(Coupon("DEF456", 20, "2025-02-28"))
controller.add_coupon(Coupon("GHI789", 30, "2022-12-31"))

controller.add_coupon_to_account("001", "ABC123")
controller.add_coupon_to_account("001", "DEF456")

controller.write_review("001", "good and tasty")



@app.post('/login', tags=["Login"])
def login(user_name: str, password: str) -> dict:
    account = controller.login(user_name, password)
    if account:
        return {"message": f"Login successful for user {user_name}"}
    else:
        return {"message": "Login failed"}

@app.get('/coupon', tags=["Coupon"])
def show_coupon():
    coupon_list = controller.show_coupon_available()
    return {"coupon_list": coupon_list}


##########
# api 1 
##########
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

##########
# api 2 
##########
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

# @app.post('/payment', tags=["Payment"])
# def process_payment(user_id: str, total_price: int, payment_method: str) -> dict:
#     user = controller.search_user_by_id(user_id)
#     if user:
#         # Here you would implement the actual payment processing logic
#         # For demonstration purposes, let's assume the payment is successful
#         return {"message": f"Payment of {total_price} units processed successfully for user {user_id} via {payment_method}"}
#     else:
#         return {"message": "User not found"}

# @app.post('/user', tags=["User"])
# def create_user(name: str, id: str):
#     controller.add_user(name, id)
#     return {"message": "user created"}

# @app.post ('/user/{user_id}', tags=["User"])
# def search_user_by_id(user_id: str):
#     user = controller.search_user_by_id(user_id)
#     if user:
#         return {"name": user.name, "id": user.id, "role": user.role}
#     else:
#         return {"message": "user not found"}

# @app.post ('/user/{user_name}', tags=["User"])
# def serach_user_by_name(user_name: str):
#     user = controller.search_user_by_name(user_name)
#     if user:
#         return {"name": user.name, "id": user.id, "role": user.role}
#     else:
#         return {"message": "user not found"}

# @app.get ('/user', tags=["User"])
# def show_user_list():
#     user_list = controller.show_user_list()
#     user_list_response = [{"name": user.name, "id": user.id, "role": user.role} for user in user_list]
#     return {"user_list": user_list_response}

# @app.get('/account', tags=["Show Account List"])
# def show_account_list():
#     account_list = controller.show_account_list()
#     account_list_response = [{"user_id": account.user.id, "role": account.user.role, "password": account.password} for account in account_list]
#     return {"account_list": account_list_response}


##########
# api 3 
##########
@app.post('/basket/{user_id}', tags=["Basket"])
def add_pizza_to_basket(user_id: str, face: str, size: str, quantity: int) -> dict:
    account = controller.search_customer_account_by_user_id(user_id)
    if account:
        if not account.basket:
            account.add_basket(Basket())
        account.basket.add_pizza(controller.create_pizza_item(face, size, quantity))
        return {"message": "Pizza added to basket"}
    else:
        return {"message": "User not found"}

@app.get('/basket/{user_id}', tags=["Basket"])
def get_basket(user_id: str):
    account = controller.search_customer_account_by_user_id(user_id)
    if account:
        if account.basket:
            pizza_list = [pizza_item for pizza_item in account.basket.pizza_list]
            return {"pizza_list": pizza_list}
        else:
            return {"message": "Basket not found"}
    else:
        return {"message": "User not found"}



@app.get('/shop', tags=["Search Shop List"])
def get_shop():
    shop_info = []
    for shop in controller.shop_list:
        shop_info.append({"shop_id_branch": shop.shop_id_branch})
    return {"Shops list": shop_info}


##########
# api 4 
##########
@app.post('/shop', tags=["Check Shop Stock"])
def check_shop_stock(shop_id_branch: int):
    stock = controller.check_stock(shop_id_branch)
    if stock:
        return {"shop_id_branch": shop_id_branch, "stock": stock}
    else:
        return {"message": "shop not found"}

##########
# api 5 
##########
@app.post('/review', tags=["Review"])
def add_review(user_id: str, review: str):
    user = controller.search_user_by_id(user_id)
    if user:
        controller.write_review(user_id, review)
        return {"message": f"Review added for user {user_id}"}
    else:
        return {"message": "User not found"}

##########
# api 6 
##########
@app.get('/review', tags=["Review"])
def see_all_review():
    reviews = controller.get_all_review()
    if reviews:
        return {"reviews": reviews}
    else:
        return {"message": "No reviews found"}


# """