from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import time
import os

app = FastAPI()
static_directory = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_directory, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_directory), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=[""],
)

class User:
    def __init__(self, id: str) -> None:
        self.__id = id
    @property
    def id(self) -> str:
        return self.__id
class Booking:
    def __init__(self, user: User, booking_time: str, mate_name: str, id: str) -> None:
        self.__user = user
        self.__booking_time = booking_time
        self.__mate_name = mate_name
        self.__id = id
    @property
    def user(self) -> User:
        return self.__user
    @property
    def booking_time(self) -> str:
        return self.__booking_time
    @property
    def mate_name(self) -> str:
        return self.__mate_name
    @property
    def id(self) -> str:
        return self.__id
    
    def pack_json(self) -> dict:
        return {
            "booking_time" : self.__booking_time,
            "mate_name" : self.__mate_name,
            "id" : self.__id 
        }

class Controller:
    def __init__(self) -> None:
        self.__user_list = [User("1"), User("2"), User("3")]
        self.__booking_list = [Booking(self.__user_list[0],time.ctime(),"pawit","1"), Booking(self.__user_list[1],time.ctime(),"kanyok","2"), Booking(self.__user_list[2], time.ctime(),"gan","3")]

    def search_user_by_id(self, user_id: str) -> User:
        for user in self.__user_list:
            if user.id == user_id:
                return user
        return None

    def search_booking_by_user(self, user: User) -> list:
        if not isinstance(user, User): return None
        bookings = []
        for booking in self.__booking_list:
            if booking.user == user:
                bookings.append(booking.pack_json())
        if len(bookings) == 0: return None
        return bookings

    def get_self_booking(self, user_id: str) -> list:
        user = self.search_user_by_id(user_id)
        if user == None: return "User not found"    
        bookings = self.search_booking_by_user(user)
        if bookings == None: return "User or Booking not found"
        return bookings
        # return self_booking_list
    
controller = Controller() 

@app.get("/get_self_booking/{user_id}")
def get_self_booking(user_id: str):
    return {"self_booking": controller.get_self_booking(user_id)}