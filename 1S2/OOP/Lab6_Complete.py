# Class Code

##################################################################################

# กำหนดรูปแบบของ user ดังนี้ {รหัสประชาชน : [ชื่อ, หมายเลขบัญชี, หมายเลข ATM, จำนวนเงิน ]}
# *** Dictionary นี้ ใช้สำหรับสร้าง user และ atm instance เท่านั้น
# user ={'1-1101-12345-12-0':['Harry Potter','1234567890','12345',20000],
#        '1-1101-12345-13-0':['Hermione Jean Granger','0987654321','12346',1000]}

# atm ={'1001':1000000,'1002':200000}

# TODO 1 : จากข้อมูลใน user ให้สร้าง instance จากข้อมูล Dictionary
# TODO :   key:value โดย key เป็นรหัสบัตรประชาชน และ value เป็นข้อมูลของคนนั้น ประกอบด้วย
# TODO :   [ชื่อ, หมายเลขบัญชี, หมายเลขบัตร ATM, จำนวนเงินในบัญชี]
# TODO :   return เป็น instance ของธนาคาร
# TODO :   และสร้าง instance ของเครื่อง ATM จำนวน 2 เครื่อง


# TODO 2 : เขียน method ที่ทำหน้าที่สอดบัตรเข้าเครื่อง ATM มี parameter 3 ตัว ได้แก่ 1) instance ของธนาคาร
# TODO     2) instance ของ atm_card 3) entered Pin ที่ user input ให้เครื่อง ATM
# TODO     return ถ้าบัตร และ Pin ถูกต้องจะได้ instance ของ account คืนมา ถ้าไม่ถูกต้องได้เป็น None
# TODO     ควรเป็น method ของเครื่อง ATM


# TODO 3 : เขียน method ที่ทำหน้าที่ฝากเงิน โดยรับ parameter 2 ตัว คือ 
# TODO     1) instance ของ account 2) จำนวนเงิน
# TODO     การทำงาน ให้เพิ่มจำนวนเงินในบัญชี และ สร้าง transaction ลงในบัญชี
# TODO     return หากการทำรายการเรียบร้อยให้ return success ถ้าไม่เรียบร้อยให้ return error
# TODO     ต้อง validate การทำงาน เช่น ตัวเลขต้องมากกว่า 0


#TODO 4 : เขียน method ที่ทำหน้าที่ถอนเงิน โดยรับ parameter 2 ตัว คือ 
# TODO     1) instance ของ account 2) จำนวนเงิน
# TODO     การทำงาน ให้ลดจำนวนเงินในบัญชี และ สร้าง transaction ลงในบัญชี
# TODO     return หากการทำรายการเรียบร้อยให้ return success ถ้าไม่เรียบร้อยให้ return error
# TODO     ต้อง validate การทำงาน เช่น ตัวเลขต้องมากกว่า 0 และ ไม่ถอนมากกว่าเงินที่มี


#TODO 5 : เขียน method ที่ทำหน้าที่โอนเงิน โดยรับ parameter 3 ตัว คือ 
# TODO     1) instance ของ account ตนเอง 2) instance ของ account ที่โอนไป 3) จำนวนเงิน
# TODO     การทำงาน ให้ลดจำนวนเงินในบัญชีตนเอง และ เพิ่มเงินในบัญชีคนที่โอนไป และ สร้าง transaction ลงในบัญชี
# TODO     return หากการทำรายการเรียบร้อยให้ return success ถ้าไม่เรียบร้อยให้ return error
# TODO     ต้อง validate การทำงาน เช่น ตัวเลขต้องมากกว่า 0 และ ไม่ถอนมากกว่าเงินที่มี

class Bank:
    def __init__(self):
        self.__user_list = []
        self.__atm_list = []
        self.__card_list = []

    @property
    def user_list(self):
        return self.__user_list
    
    @property
    def atm_list(self):
        return self.__atm_list
    
    @property
    def card_list(self):
        return self.__card_list
    
class ATM:
    atm_money = 1000000
    limit_money = 40000

    def __init__(self, atm_id):
        self.__atm_id = atm_id

    @property
    def atm_id(self):
        return self.__atm_id
    
    def insert_card(self, card, account, pin_number):
        if pin_number == card.pin_number:
            return print(card.card_no, account.account_id, "Success")
        return None
    
    def deposit(self, atm, account, money):
        if money > 0:
            account.set_balance += money
            account.transaction_list.append(Transaction('D', money, account.balance, atm.atm_id, account.account_id))
            ATM.atm_money += money
            return account.balance
        return "Error"
    
    def withdraw(self, atm, account, money):
        if money > account.balance:
            return "Error, Money in account is not enough"
        elif money > 0:
            account.set_balance -= money
            account.transaction_list.append(Transaction('W', money, account.balance, atm.atm_id, account.account_id))
            ATM.atm_money -= money
            return account.balance
        return "Error"
    
    def transfer(self, atm, account1, account2, money):
        if money > account1.balance:
            return "Error, money in account is not enough"
        elif money > 0:
            account1.set_balance -= money
            account2.set_balance += money
            account1.transaction_list.append(Transaction('T', money, account1.balance, atm.atm_id, account1.account_id))
            account2.transaction_list.append(Transaction('T', money, account2.balance, atm.atm_id, account2.account_id))
            return account1.balance, account2.balance
        return "Error"
    
class User:
    def __init__(self, citizen_id, name):
        self.__citizen_id = citizen_id
        self.__name = name
        self.__account_list = []

    @property
    def citizen_id(self):
        return self.__citizen_id

    @property
    def name(self):
        return self.__name
    
    @property
    def account_list(self):
        return self.__account_list
    
class Account:
    def __init__(self, account_id, user, balance):
        self.__account_id = account_id
        self.__user = user
        self.__balance = balance
        self.__transaction_list = []

    @property
    def account_id(self):
        return self.__account_id
    
    @property
    def user(self):
        return self.__user
    
    @property
    def balance(self):
        return self.__balance
    
    @balance.setter
    def set_balance(self, balance):
        self.__balance = balance

    @property
    def transaction_list(self):
        return self.__transaction_list
    
class ATM_card:
    pin_number = 1234
    def __init__(self, card_no):
        self.__card_no = card_no

    @property
    def card_no(self):
        return self.__card_no
    
class Transaction:
    def __init__(self, type, money, balance, atm_id, account_id):
        self.__type = type
        self.__money = money
        self.__balance = balance
        self.__atm_id = atm_id
        self.__account_id = account_id
      
    def __str__(self):
        if self.__type == 'D':
            return f"{self.__type} : {self.__atm_id}- +{self.__money}-{self.__balance}"
        elif self.__type == 'W':
            return f"{self.__type} : {self.__atm_id}- -{self.__money}-{self.__balance}"
        elif self.__type == 'T':
            return f"{self.__type} : {self.__atm_id}- -{self.__money}-{self.__balance}"
        else:
            return "Unknown Transaction Type"

    @property
    def data(self):
        return self.__data
    
    @property
    def type(self):
        return self.__type
    
    @property
    def money(self):
        return self.__money

    @property
    def balance(self):
        return self.__balance
    
    @property
    def time(self):
        return self.__time
    
    @property
    def atm_id(self):
        return self.__atm_id
    
    @property
    def account_id(self):
        return self.__account_id
    
bank = Bank()

user1 = User('1-1101-12345-12-0', 'Harry Potter')
user2 = User('1-1101-12345-13-0', 'Hermione Jean Granger')

account1 = Account('1234567890', user1, 20000)
account2 = Account('0987654321', user2, 1000)
account_list = [account1, account2]

card1 = ATM_card('12345')
card2 = ATM_card('12346')
card_list = [card1, card2]

atm1 = ATM('1001')
atm2 = ATM('1002')

# Test case #1 : ทดสอบ การ insert บัตร ที่เครื่อง atm เครื่องที่ 1 โดยใช้บัตร atm ของ harry
# และ Pin ที่รับมา เรียกใช้ function หรือ method จากเครื่อง ATM 
# ผลที่คาดหวัง : พิมพ์ หมายเลขบัตร ATM อย่างถูกต้อง และ หมายเลข account ของ harry อย่างถูกต้อง
# Ans : 12345, 1234567890, Success
print("Test case #1")

atm1.insert_card(card1, account1, 1234)

print("----------------------------------------")

# Test case #2 : ทดสอบฝากเงินเข้าในบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 1000 บาท
# ให้เรียกใช้ method ที่ทำการฝากเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Hermione ก่อนฝาก หลังฝาก และ แสดง transaction
# Hermione account before test : 1000
# Hermione account after test : 2000
print("Test case #2")

print("Hermione account before test : ", account2.balance)
atm2.deposit(atm2, account2, 1000)
print("Hermione account after test : ", account2.balance)

for gettransaction in account2.transaction_list:
    print("Hermione Transaction : ", gettransaction)

print("----------------------------------------")

# Test case #3 : ทดสอบฝากเงินเข้าในบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน -1 บาท
# ผลที่คาดหวัง : แสดง Error
print("Test case #3")

print(atm2.deposit(atm2, account2, -1))

print("----------------------------------------")


# Test case #4 : ทดสอบการถอนเงินจากบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 500 บาท
# ให้เรียกใช้ method ที่ทำการถอนเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Hermione ก่อนถอน หลังถอน และ แสดง transaction
# Hermione account before test : 2000
# Hermione account after test : 1500
print("Test case #4")

print("Hermione account before test : ", account2.balance)
atm2.withdraw(atm2, account2, 500)
print("Hermione account after test : ", account2.balance)

for gettransaction in account2.transaction_list:
    print("Hermione Transaction : ", gettransaction)

print("----------------------------------------")

# Test case #5 : ทดสอบถอนเงินจากบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 2000 บาท
# ผลที่คาดหวัง : แสดง Error
print("Test case #5")

print(atm2.withdraw(atm2, account2, 2000))

print("----------------------------------------")

# Test case #6 : ทดสอบการโอนเงินจากบัญชีของ Harry ไปยัง Hermione จำนวน 10000 บาท ในเครื่อง atm เครื่องที่ 2
# ให้เรียกใช้ method ที่ทำการโอนเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Harry ก่อนถอน หลังถอน และ แสดงจำนวนเงินในบัญชีของ Hermione ก่อนถอน หลังถอน แสดง transaction
# Harry account before test : 20000
# Harry account after test : 10000
# Hermione account before test : 1500
# Hermione account after test : 11500
print("Test case #6")

print("Harry account before test : ", account1.balance)
print("Hermione account before test : ", account2.balance)
atm2.transfer(atm2, account1, account2, 10000)
print("Harry account after test : ", account1.balance)
print("Hermione account after test : ", account2.balance)

print("----------------------------------------")


# Test case #7 : แสดง transaction ของ Hermione ทั้งหมด 
# กำหนดให้เรียกใช้ method __str__() เพื่อใช้คำสั่งพิมพ์ข้อมูลจาก transaction ได้
# ผลที่คาดหวังt1500
print("Test case #7")

for gettransaction in account2.transaction_list:
       print("Hermione Transaction : ", gettransaction)