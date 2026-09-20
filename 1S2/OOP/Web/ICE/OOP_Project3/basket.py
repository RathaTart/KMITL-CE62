from pizza import Pizza, Pizza_item
from drink import Drink, Drink_item
from user import User
# from controller import Controller

class Basket :
    def __init__(self) -> None:
        self.__owner = User
        self.__pizza_list = []
        self.__drink_list = []

    @property
    def owner(self) -> User:
        return self.__owner
    
    @property
    def pizza_list(self) -> list:
        return self.__pizza_list
    
    @property
    def drink_list(self) -> list:
        return self.__drink_list
    
    def add_pizza(self, item: Pizza_item) -> None:
        for pizza in self.__pizza_list:
            if item.pizza == pizza.pizza and item.size == pizza.size:
                pizza.quantity += item.quantity
                break
        else:
            self.__pizza_list.append(item)

    def add_drink(self, item: Drink_item) -> None:
        for drink in self.__drink_list:
            if item.drink == drink.drink and item.size == drink.size:
                drink.quantity += item.quantity
                break
        else:
            self.__drink_list.append(item)

    def remove_pizza(self, item: Pizza_item) -> None:
        self.__pizza_list.remove(item)

    def remove_drink(self, item: Drink_item) -> None:
        self.__drink_list.remove(item)
    
    def edit_pizza(self, item: Pizza_item, new_size: str, new_quantity: int) -> None:
        for pizza in self.__pizza_list:
            if pizza == item:
                pizza.quantity = new_quantity
                pizza.size = new_size
                break
            
    def edit_drink(self, item: Drink_item, new_size: str, new_quantity: int) -> None:
        for drink in self.__drink_list:
            if drink == item:
                drink.quantity = new_quantity
                drink.size = new_size
                break

    def get_individual_price_pizza(self, item: Pizza_item) -> int:
        if item.size == "S" or item.size == "s":
            pizza_price = item.pizza.price * item.quantity
        elif item.size == "M" or item.size == "m":
            pizza_price = (item.pizza.price + 30)* item.quantity 
        elif item.size == "L" or item.size == "l":
            pizza_price = (item.pizza.price + 50)* item.quantity
        return pizza_price
    
    def get_individual_price_drink(self, item: Drink_item) -> int:
        if item.size == "S" or item.size == "s":
            drink_price = item.drink.price * item.quantity
        elif item.size == "M" or item.size == "m":
            drink_price = (item.drink.price + 10)* item.quantity
        elif item.size == "L" or item.size == "l":
            drink_price = (item.drink.price + 20)* item.quantity
        return drink_price
    
    def get_total_price(self) -> int:
        total_price = 0
        for pizza in self.__pizza_list:
            if pizza :
                total_price += self.get_individual_price_pizza(pizza)
        for drink in self.__drink_list:
            if drink : 
                total_price += self.get_individual_price_drink(drink)
        return total_price