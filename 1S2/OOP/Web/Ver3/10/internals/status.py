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