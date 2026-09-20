import time

class Coupon:
    current_date = time.strftime("%Y-%m-%d")

    def __init__(self, code: str, discount: int, date_available: str) -> None:
        self.__code = code
        self.__discount = discount
        self.__date_available = date_available
    
    @property
    def code(self) -> str:
        return self.__code
    
    @property
    def discount(self) -> int:
        return self.__discount

    @property
    def date_available(self) -> str:
        return self.__date_available
    
    def is_valid(self) -> bool:
        return self.__date_available > time.strftime("%Y-%m-%d")
    
    