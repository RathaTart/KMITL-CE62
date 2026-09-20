class Shop:
    def __init__(self, shop_id_branch: int) -> None:
        self.__shop_id_branch = shop_id_branch
        self.__shop_stock = Shop_stock()
    
    @property
    def shop_id_branch(self):
        return self.__shop_id_branch
    
    @property
    def shop_stock(self):
        return self.__shop_stock
    
    def reduce_pizza_stock(self, quantity: int) -> None:
        self.__shop_stock.__pizza_amount -= quantity
    
    def reduce_drink_stock(self, quantity: int) -> None:
        self.__shop_stock.__drink_amount -= quantity
    
    def add_pizza_stock(self, quantity: int) -> None:
        self.__shop_stock.__pizza_amount += quantity

    def add_drink_stock(self, quantity: int) -> None:
        self.__shop_stock.__drink_amount += quantity

    def restock(self) -> None:
        self.__shop_stock.__pizza_amount = self.__shop_stock.dialy_stock
        self.__shop_stock.__drink_amount = self.__shop_stock.dialy_stock

class Shop_stock():
    dialy_stock = 10
    def __init__(self):
        self.__pizza_amount = self.dialy_stock
        self.__drink_amount = self.dialy_stock

    @property
    def pizza_amount(self):
        return self.__pizza_amount
    
    @property
    def drink_amount(self):
        return self.__drink_amount