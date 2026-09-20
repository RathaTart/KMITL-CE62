from pizza import Pizza, Pizza_item
from user import User
# from controller import Controller

class Basket :
    def __init__(self) -> None:
        self.__owner = User
        self.__pizza_list = []

    @property
    def owner(self) -> User:
        return self.__owner
    
    @property
    def pizza_list(self) -> list:
        return self.__pizza_list
    
    
    def add_pizza(self, item: Pizza_item) -> None:
        for pizza in self.__pizza_list:
            if item.pizza == pizza.pizza and item.size == pizza.size:
                pizza.quantity += item.quantity
                break
        else:
            self.__pizza_list.append(item)

    def remove_pizza(self, item: Pizza_item) -> None:
        self.__pizza_list.remove(item)
    
    def edit_pizza(self, item: Pizza_item, new_size: str, new_quantity: int) -> None:
        for pizza in self.__pizza_list:
            if pizza == item:
                pizza.quantity = new_quantity
                pizza.size = new_size
                break

    def get_individual_price(self, item: Pizza_item) -> int:
        if item.size == "S":
            pizza_price = item.pizza.price * item.quantity
        elif item.size == "M":
            pizza_price = (item.pizza.price + 30)* item.quantity 
        elif item.size == "L":
            pizza_price = (item.pizza.price + 50)* item.quantity
        return pizza_price
    
    def get_total_price(self) -> int:
        total_price = 0
        for pizza in self.__pizza_list:
            total_price += self.get_individual_price(pizza)
        return total_price