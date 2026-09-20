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
    
    @quantity.setter
    def quantity(self, quantity: int) -> None:
        self.__quantity = quantity