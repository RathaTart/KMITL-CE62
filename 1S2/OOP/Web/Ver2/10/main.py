from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import time

app = FastAPI()

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")

class PizzaOrder(BaseModel):
    name: str
    size: str
    toppings: List[str]
    quantity: int

menu_items = {
    "pepperoni": {"name": "Pepperoni", "price": 10.99},
    "margherita": {"name": "Margherita", "price": 9.99},
    "vegetarian": {"name": "Vegetarian", "price": 11.99}
}

@app.post("/order/")
async def place_order(order: PizzaOrder):
    if order.name not in menu_items:
        raise HTTPException(status_code=404, detail="Menu item not found")
    
    total_price = menu_items[order.name]["price"] * order.quantity
    
    confirmation_message = f"Order confirmed: {order.quantity} {order.size} {order.name} pizza(s) with {', '.join(order.toppings)}. Total price: ${total_price}"
    
    return {"message": confirmation_message}

@app.get("/menu/")
async def get_menu():
    return menu_items


