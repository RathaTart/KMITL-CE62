from basket import Basket

class Order:
    def __init__(self,basket: Basket) :
        self.__basket = Basket()
        self.__payment_status = False
