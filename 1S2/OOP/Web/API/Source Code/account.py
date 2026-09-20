
from basket import Basket
from order import Order
from user import User
  
class Status:
    def __init__(self, status: str, date: str) -> None:
        self.__status = status
        self.__date = date
    
    @property
    def status(self) -> str:
        return self.__status
    
    @property
    def date(self) -> str:
        return self.__date

class Account :
    def __init__ (self, user: User, password: str) -> None:
        self.__user = user
        self.__password = password
        self.__address = ''
        self.__transaction_list = []
    
    @property
    def user(self) -> User:
        return self.__user
    
    @property
    def password(self) -> str:
        return self.__password
    
    @property
    def address(self) -> str:
        return self.__address
    
    @property
    def transaction_list(self) -> list:
        return self.__transaction_list
    

    def add_address(self, address: str) -> None:
        self.__address = address
    
class Customer_account(Account):
    def __init__(self, user: User, password: str) -> None:
        super().__init__(user, password)
        self.__basket = Basket()
        self.__success_order = []
        self.__unsuccess_order = []
        self.__coupon_list = []

    @property
    def basket(self) -> Basket:
        return self.__basket
     
    @property
    def success_order(self) -> list:
        return self.__success_order
    
    @property
    def unsuccess_order(self) -> list:
        return self.__unsuccess_order
    
    @property
    def coupon_list(self) -> list:
        return self.__coupon_list
    
    def add_coupon(self, coupon: str) -> None:
        self.__coupon_list.append(coupon)
    
    def create_order(self) -> None:
        order = Order(self.__basket)

class Shop_account(Account) :
    def __init__(self, user: User, password: str) -> None:
        super().__init__(user, password)
        self.__branch = []
    
    @property
    def branch(self) -> list:
        return self.__branch
    
    def update_order_status(self, order_id: str, status: str) -> None:
        pass






