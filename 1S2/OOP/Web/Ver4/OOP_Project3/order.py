from basket import Basket
from payment import Payment
from coupon import Coupon
from shop import Shop, Shop_stock
import time
import uuid

class Order:
    def __init__(self, basket: Basket, address: str):
        self.__id = str(uuid.uuid4())
        self.__basket = basket
        self.__payment = None
        self.__coupon = None
        self.__deli_or_pick: str = None
        self.__address = address
        self.__perfer_shop: Shop = None
        self.__time = time.strftime("%Y-%m-%d %H:%M:%S")

    @property
    def id(self) -> uuid:
        return self.__id

    @property
    def basket(self) -> Basket:
        return self.__basket
    
    @property
    def payment(self) -> Payment:
        return self.__payment
    
    @property
    def coupon(self) -> Coupon:
        return self.__coupon
    
    def apply_coupon(self, coupon: Coupon) -> None:
        self.__coupon = coupon
    
    def remove_coupon(self) -> None:
        self.__coupon = None

    def get_net_price(self) -> int:
        total_price = self.__basket.get_total_price()
        if self.__coupon:
            if self.coupon.is_valid():
                total_price -= self.__coupon.discount
        return total_price

    def create_payment(self, payment_method:str) -> None:
        self.__payment = Payment(self.get_net_price(), payment_method)

    # def process_payment(self) -> None:
    #     self.__payment.process_payment()
    #     self.__basket.pizza_list.clear()
    #     self.__basket.drink_list.clear()
    #     self.__coupon = None
    #     self.__payment = None
    #     return self.__payment.status

