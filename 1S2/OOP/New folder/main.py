from typing import Optional
from fastapi import FastAPI

class Controller:
    def __init__(self):
        self.user_list = []
        self.shop_list = []

    def check_stock(self,name):
        for shop in self.shop_list:
            if shop.name == name:
                return shop.get_stock()
    def add_shop(self,id,name):
        stock = shop_stock()
        shop = Shop(id, name, stock)
        self.shop_list.append(shop)
    def shop_list(self):
        temp = []
        for shop in self.shop_list:
            temp.append(shop.name)
        return temp


class Shop:
    def __init__(self,id, name,stockinstance):
        self.id = id
        self.name = name
        self.stock = stockinstance
    def add_stock(self, item):
        self.__stock.append(item)
    def get_stock(self):
        return self.stock.pizza_list_amount, self.stock.drink_list_amount
    
class shop_stock:
    def __init__(self):
        self.pizza_list_amount = ["pepporoni", "cheese", "hawaiian"]
        self.drink_list_amount = ["coke"]

site = Controller()
pizzashop = site.add_shop(1,"shop1")
# print(site.shop_list())
print(site.check_stock("shop1"))

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/hello")
def hello(name:str):
    return {"Hello": name}

@app.get("/test")
def test(request:str, reply:str):
    return {"Request": request, "Reply": reply}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/shop")
def get_stock(shop:str):
    return {"stock": site.check_stock(shop)}

# @app.get("/shop")
# def get_shop_list():
#     return {site.shop_list}