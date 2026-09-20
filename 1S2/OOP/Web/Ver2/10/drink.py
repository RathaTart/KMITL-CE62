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

class Drink_item:
    def __init__(self, drink: Drink, size: str, quantity: int) -> None:
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