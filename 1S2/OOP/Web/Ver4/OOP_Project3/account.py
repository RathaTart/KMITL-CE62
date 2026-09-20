
from basket import Basket
from order import Order
from user import User
from coupon import Coupon

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
        self.__preferd_shop = None
        self.__uncompleted_order = None
        self.__completed_order_list = []
        self.__coupon_list = []

    @property
    def basket(self) -> Basket:
        return self.__basket
    
    @property
    def address(self) -> str:
        return self.__address
    
    @property
    def uncompleted_order(self) -> Order:
        return self.__uncompletd_order
     
    @property
    def order_list(self) -> list:
        return self.__completed_order_list
    
    @property
    def coupon_list(self) -> list:
        return self.__coupon_list
    
    
    def add_address(self, address: str) -> None:
        self.__address = address
    
    def add_coupon(self, coupon: str) -> None:
        self.__coupon_list.append(coupon)

    def remove_coupon(self, coupon: str) -> None:
        self.__coupon_list.remove(coupon)
        
    def create_order(self) -> None:
        self.__uncompletd_order = Order(self.__basket, self.__address)

    # def pre

    def search_coupon_by_code(self, code: str) -> Coupon:
        for coupon in self.__coupon_list:
            if coupon.code == code:
                return coupon
        raise ValueError("Coupon not found")

class Shop_account(Account) :
    def __init__(self, user: User, password: str) -> None:
        super().__init__(user, password)
        self.__branch = []
    
    @property
    def branch(self) -> list:
        return self.__branch
    
    def update_order_status(self, order_id: str, status: str) -> None:
        pass






