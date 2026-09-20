class Pizza :
    def __init__(self, name: str, price: int) -> None:
        self.__face = name
        self.__price = price
    
    @property
    def face(self) -> str:
        return self.__face
    
    @property
    def price(self) -> int:
        return self.__price
    
class Pizza_item :
    def __init__(self, pizza: Pizza, size : str, quantity: int) -> None:
        self.__pizza = pizza
        self.__size = size
        self.__quantity = quantity
        
    @property
    def pizza(self) -> Pizza:
        return self.__pizza
    
    @property
    def size(self) -> str:
        return self.__size
    
    @property
    def quantity(self) -> int:
        return self.__quantity
    
class Drink:
    def __init__(self):
        self.__drink_type = []
        self.__size = []
    
    @property
    def drink_type(self):
        return self.__drink_type
    
    @property
    def size(self):
        return self.__size
    
class Basket :
    def __init__(self) -> None:
        self.__pizza_list = []

    def add_pizza(self, pizza: Pizza_item) -> None:
        self.__pizza_list.append(pizza)

    def remove_pizza(self, pizza: Pizza_item) -> None:
        self.__pizza_list.remove(pizza)

    def get_total_price(self) -> int:
        total_price = 0
        for pizza in self.__pizza_list:
            total_price += pizza.pizza.price * pizza.quantity
        return total_price

pizza1 = Pizza("pepperoni", 10.99)
pizzaorder = Pizza_item(pizza1, "L", 2)
Basket1 = Basket()
Basket1.add_pizza(pizzaorder)
print(Basket1.get_total_price())
