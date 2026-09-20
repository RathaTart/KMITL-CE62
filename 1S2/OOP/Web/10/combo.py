from pizza import Pizza
from drink import Drink

class Combo:
    def __init__(self, pizza: Pizza, drink: Drink) -> None:
        self.__pizza = pizza
        self.__drink = drink
    
    @property
    def pizza(self) -> Pizza:
        return self.__pizza
    
    @property
    def drink(self) -> Drink:
        return self.__drink
    
    def add_pizza(self, pizza: Pizza) -> None:
        pass

    def add_drink(self, drink: Drink) -> None:
        pass