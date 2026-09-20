class Drink :
    def __init__(self, name: str, price: int) -> None:
        self.__name = name
        self.__price = price
    
    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def price(self) -> int:
        return self.__price
    
class Drink_item :
    def __init__(self, drink: Drink, size : str, quantity: int) -> None:
        self.__drink = drink
        self.__size = size
        self.__quantity = quantity
        
    @property
    def drink(self) -> Drink:
        return self.__drink
    
    @property
    def size(self) -> str:
        return self.__size
    
    @property
    def quantity(self) -> int:
        return self.__quantity
    
    @quantity.setter
    def quantity(self, quantity: int) -> None:
        self.__quantity = quantity