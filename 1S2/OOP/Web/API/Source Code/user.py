class User:
    def __init__(self, name : str, id:str, role:str) -> None:
        self.__name = name
        self.__id = id
        self.__role = role

    @property
    def name(self) -> str:
        return self.__name
    
    @property
    def id(self) -> str:
        return self.__id
    
    @property
    def role(self) -> str:
        return self.__role