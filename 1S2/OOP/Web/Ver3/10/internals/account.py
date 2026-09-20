
from basket import Basket
from order import Order
from user import User


class Account :
    def __init__ (self, user: User, password: str) -> None:
        self.__user = user
        self.__password = password
    
    @property
    def user(self) -> User:
        return self.__user
    
    @property
    def password(self) -> str:
        return self.__password
    
class Customer_account(Account):
    def __init__(self, user: User, password: str) -> None:
        super().__init__(user, password)
        self.__basket = Basket()
        self.__address = ''
        self.__order_list = []
        self.__coupon_list = []

    @property
    def basket(self) -> Basket:
        return self.__basket
    
    @property
    def address(self) -> str:
        return self.__address
     
    @property
    def order_list(self) -> list:
        return self.__order_list
    
    @property
    def coupon_list(self) -> list:
        return self.__coupon_list
    
    def add_address(self, address: str) -> None:
        self.__address = address
    
    def add_coupon(self, coupon: str) -> None:
        self.__coupon_list.append(coupon)
    
    def create_order(self) -> None:
        self.__order_list.append(Order(self.__basket))

class Shop_account(Account) :
    def __init__(self, user: User, password: str) -> None:
        super().__init__(user, password)
        self.__branch = []
    
    @property
    def branch(self) -> list:
        return self.__branch
    
    def update_order_status(self, order_id: str, status: str) -> None:
        pass






