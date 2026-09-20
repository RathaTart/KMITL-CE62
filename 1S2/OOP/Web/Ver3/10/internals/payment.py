class Payment :
    def __init__(self, amount: int, method: str) -> None:
        self.__amount = amount
        self.__method = method
        self.__status = False

    @property
    def amount(self) -> int:
        return self.__amount
    
    @property
    def method(self) -> str:
        return self.__method
    
    @property
    def status(self) -> bool:
        return self.__status
    
    def process_payment(self) -> None:
        self.__status = True