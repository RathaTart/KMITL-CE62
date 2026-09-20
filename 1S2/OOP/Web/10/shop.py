class Shop:
    def __init__(self, shop_id_branch: int) -> None:
        self.__shop_id_branch = shop_id_branch
        self.__shop_stock = []
    
    @property
    def shop_id_branch(self):
        return self.__shop_id_branch
    
    @property
    def shop_stock(self):
        return self.__shop_stock

    def add_stock(self, stock_items: list) -> None:
        for item, quantity in stock_items:
            self.__shop_stock.append((item, quantity))
            
    def get_stock(self) -> list:
        return self.__shop_stock

    def check_stock():
        pass

class Shop_stock(Shop):
    def __init__(self):
        Shop.__init__(self)
        self.__pizza_list_amount = []
        self.__drink_list_amount = []

    @property
    def pizza_list_amount(self):
        return self.__pizza_list_amount
    
    @property
    def drink_list_amount(self):
        return self.__drink_list_amount