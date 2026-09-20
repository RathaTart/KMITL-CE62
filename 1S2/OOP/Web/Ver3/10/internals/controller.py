from user import User
from account import Account, Customer_account, Shop_account
from shop import Shop
from coupon import Coupon
from basket import Basket
from pizza import Pizza, Pizza_item

class Controller :
    def __init__(self) -> None:
        self.__user_list = []
        self.__customer_account_list = []
        self.__shop_account_list = []
        self.__shop_list = []
        self.__pizza_list = []
        self.__coupon_list = []
        self.__review_list = []

    @property
    def user_list(self) -> list:
        return self.__user_list
    
    @property
    def customer_account_list(self) -> list:
        return self.__customer_account_list
    
    @property
    def shop_list(self) -> list:
        return self.__shop_list
    
    @property
    def pizza_list(self) -> list:
        return self.__pizza_list
    
    @property
    def coupon_list(self) -> list:
        return self.__coupon_list
    
    @property
    def review_list(self) -> list:
        return self.__review_list
    
    def add_customer_account(self, user_name: str, password: str) -> Customer_account:
        user = self.search_user_by_name(user_name)
        if user and user.role == "customer":
            customer_account = Customer_account(user, password)
            self.__customer_account_list.append(customer_account)
            return customer_account
        else:
            return ValueError("User not found or not a customer")
        
    def add_shop_account(self, user_name: str, password: str) -> Shop_account:
        user = self.search_user_by_id(user_name)
        if user and user.role == "shop":
            shop_account = Shop_account(user, password)
            self.__shop_account_list.append(shop_account)
            return shop_account
        else:
            return ValueError("User name not found")

    def add_user(self, name: str, role: str, password: str) -> None:
        self.__user_list.append(User(name, role))
        if role == "customer":
            self.add_customer_account(name, password)
        elif role == "shop":
            self.add_shop_account(name, password)

    def add_shop(self, shop_id_branch: int) -> Shop:
        shop = Shop(shop_id_branch)
        if isinstance(shop, Shop) :
            self.__shop_list.append(shop)
            return shop
        else:
            raise TypeError("Is not shop class")

    def show_user_list(self) -> list:
        return self.__user_list
    
    def show_account_list(self) -> list:
        return self.__customer_account_list + self.__shop_account_list
    
    def view_pizza_list(self, shop_id_branch: int) -> list:
        shop = self.search_shop_by_id(shop_id_branch)
        if shop:
            pizza_list = shop.pizza_list
            return pizza_list
        else:
            return "No pizza avaliable"

    def view_drink_list(self, shop_id_branch: int) -> list:
        shop = self.search_shop_by_id(shop_id_branch)
        if shop:
            drink_list = shop.drink_list
            return drink_list
        else:
            return "No drinks available"

    def search_user_by_id(self, user_id: str) -> User:
        for user in self.user_list:
            if user.id == user_id:
                return user
        return ValueError(f"No user ID:'{user_id}'")

    def search_user_by_name(self, name: str) -> User:
        for user in self.user_list:
            if user.name == name:
                return user
        raise ValueError(f"User with name '{name}' not found")
    
    def search_account_by_name(self, name: str) -> Account:
        for account in self.__customer_account_list + self.__shop_account_list:
            if account.user.name == name:
                return account
        return ValueError("Account name not found")
    
    def search_account_by_user_id(self, user_id: str) -> Account:
        for account in self.__customer_account_list + self.__shop_account_list:
            if account.user.id == user_id:
                return account
        return ValueError("Account ID not found")
    
    def get_user_id_by_name(self, name: str) -> str:
        for user in self.user_list:
            if user.name == name:
                return user.id
        return ValueError("User not found")
    
    def search_shop_by_id(self, shop_id_branch: int) -> Shop:
        for shop in self.__shop_list:
            if shop.shop_id_branch == shop_id_branch:
                return shop
        return ValueError(f"Shop ID:'{shop_id_branch}' not found")
    
    def check_stock(self, shop_id_branch: int) -> list:
        for shop in self.shop_list:
            if shop.shop_id_branch == shop_id_branch:
                return shop.shop_stock
        return ValueError(f"Shop with id '{shop_id_branch}' not found")
            
    def add_stock_to_shop(self, shop_id_branch: int, stock_items: list) -> None:
        for shop in self.__shop_list:
            if shop.shop_id_branch == shop_id_branch:
                shop.add_stock(stock_items)    
            return ValueError(f"Shop with id '{shop_id_branch}' not found")
    
    def add_pizza(self, name: str, price: int) -> Pizza:
        pizza = Pizza(name, price)
        self.__pizza_list.append(pizza)
        return pizza
    
    def get_pizza(self, face: str) -> Pizza:
        for pizza in self.__pizza_list:
            if pizza.face == face:
                return pizza
        raise ValueError("Pizza not found")
    
    def create_pizza_item(self, face: str , size: str, quantity: int) -> Pizza_item:
        pizza = self.get_pizza(face)
        return Pizza_item(pizza, size, quantity)

    def calculated_total_price(self, user_id: str) -> int:
        pass

    def payment(self, user_id: int, total_price: int) -> None:
        pass

    def select_payment_method(self, user_id: int, payment_method: str) -> None:
        pass

    def add_coupon(self, coupon: Coupon) -> None:
        self.__coupon_list.append(coupon)

    def remove_coupon(self, coupon: Coupon) -> None:
        self.__coupon_list.remove(coupon)
    
    def search_coupon_by_code(self, code: str) -> Coupon:
        for coupon in self.__coupon_list:
            if coupon.code == code:
                return coupon
        raise ValueError("Coupon not found")
    
    def add_coupon_to_account(self, user_id: str, coupon_code: str) -> None:
        account = self.search_account_by_user_id(user_id)
        coupon = self.search_coupon_by_code(coupon_code)
        account.add_coupon(coupon)

    def write_review(self, user_id: str, review: str) -> None:
        # write review to the all shop
        if review:
            self.__review_list.append((user_id, review))

    def get_all_review(self) -> list:
        reviews = []
        for user_review in self.__review_list:
            reviews.append({"user_id": user_review[0], "review": user_review[1]})
        return reviews