# Class Code
class Bank:
    def __init__(self):
        self.__ATM_list = []
        self.__user_list = []

    @property
    def ATM_list(self):
        return self.__ATM_list
    @property
    def user_list(self):
        return self.__user_list
    def add_ATM_list(self, ATM_list):
        self.__ATM_list.append(ATM_list)
    def add_user_list(self, user_list):
        self.__user_list.append(user_list)

class ATM:
    def __init__(self, ATM_number, balance):
        self.__ATM_number = ATM_number
        self.__balance = balance
    @property
    def ATM_number(self):
        return self.__ATM_number
    @property
    def balance(self):
        return self.__balance
    @balance.setter
    def balance(self, value):
        self.__balance = value
    def insert_card(self,bank, card_number, account_number):
        for user in bank.user_list:
            for account in user.account_list:
                if account.account_number == account_number and account.card_number == card_number:
                    return "Success"
        return "Error"
    def deposit(self, account, deposit_amount):
        if deposit_amount > 0:
            account.balance += deposit_amount
            account.statement.append(Transaction("D", account.balance, self.ATM_number, deposit_amount))
            return "Success"
        return "Error"

class User:
    def __init__(self, ID_number, name):
        self.__ID_number = ID_number
        self.__name = name
        self.__account_list = []

    @property
    def ID_number(self):
        return self.__ID_number
    @property
    def name(self):
        return self.__name
    @property
    def account_list(self):
        return self.__account_list
    
    def add_account(self, account):
        self.__account_list.append(account)

class Account:
    def __init__(self, account_number, card_number, balance):
        self.__account_number = account_number
        self.__card_number = card_number
        self.__balance = balance
        self.__transaction = []

    @property
    def account_number(self):
        return self.__account_number
    @property
    def card_number(self):
        return self.__card_number
    @property
    def balance(self):
        return self.__balance
    @balance.setter
    def balance(self, value):
        self.__balance = value
    @property
    def statement(self):
        return self.__transaction
    
class Card:
    def __init__(self, card_number, card_pin):
        self.__card_number = card_number
        self.__card_pin = card_pin
    @property
    def card_number(self):
        return self.__card_number
    @property
    def pin(self):
        return self.__card_pin
    
class Transaction:
    def __init__(self, transaction_type, balance, atm_number, account_number):
        self.__transaction_type = transaction_type
        self.__balance = balance
        self.__atm_number = atm_number
        self.__account_number = account_number
    @property
    def transaction_type(self):
        return self.__transaction_type 
    @property
    def balance(self):
        return self.__balance
    @property
    def atm_number(self):
        return self.__atm_number
    @property
    def account_number(self):
        return self.__account_number
    



##################################################################################

# กำหนดรูปแบบของ user ดังนี้ {รหัสประชาชน : [ชื่อ, หมายเลขบัญชี, หมายเลข Card, จำนวนเงิน ]}
# *** Dictionary นี้ ใช้สำหรับสร้าง user และ atm instance เท่านั้น
user ={'1-1101-12345-12-0':['Harry Potter','1234567890','12345',20000],
       '1-1101-12345-13-0':['Hermione Jean Granger','0987654321','12346',1000]}

atm ={'1001':1000000,'1002':200000}

# TODO 1 : จากข้อมูลใน user ให้สร้าง instance จากข้อมูล Dictionary
# TODO :   key:value โดย key เป็นรหัสบัตรประชาชน และ value เป็นข้อมูลของคนนั้น ประกอบด้วย
# TODO :   [ชื่อ, หมายเลขบัญชี, หมายเลขบัตร ATM, จำนวนเงินในบัญชี]
# TODO :   return เป็น instance ของธนาคาร
# TODO :   และสร้าง instance ของเครื่อง ATM จำนวน 2 เครื่อง

def create_instance(user, atm):
    bank_temp = Bank()
    for key, value in user.items():
        user_temp = User(key, value[0])
        account_temp = Account(value[1], value[2], value[3])
        user_temp.add_account(account_temp)
        bank_temp.add_user_list(user_temp)
    for key, value in atm.items():
        atm_temp = ATM(key, value)
        bank_temp.add_ATM_list(atm_temp)
    return bank_temp
bank = create_instance(user, atm)

# TODO 2 : เขียน method ที่ทำหน้าที่สอดบัตรเข้าเครื่อง ATM มี parameter 3 ตัว ได้แก่ 1) instance ของธนาคาร
# TODO     2) instance ของ atm_card 3) entered Pin ที่ user input ให้เครื่อง ATM
# TODO     return ถ้าบัตร และ Pin ถูกต้องจะได้ instance ของ account คืนมา ถ้าไม่ถูกต้องได้เป็น None
# TODO     ควรเป็น method ของเครื่อง ATM
person = bank.user_list[0].account_list[0]
print(person.card_number, person.account_number, bank.ATM_list[0].insert_card(bank, "12345", "1234567890"))
print('-------------------------')

# TODO 3 : เขียน method ที่ทำหน้าที่ฝากเงิน โดยรับ parameter 2 ตัว คือ 
# TODO     1) instance ของ account 2) จำนวนเงิน
# TODO     การทำงาน ให้เพิ่มจำนวนเงินในบัญชี และ สร้าง transaction ลงในบัญชี
# TODO     return หากการทำรายการเรียบร้อยให้ return success ถ้าไม่เรียบร้อยให้ return error
# TODO     ต้อง validate การทำงาน เช่น ตัวเลขต้องมากกว่า 0

# Deposit 1000 to Hermione 
print(bank.user_list[1].name, bank.user_list[1].account_list[0].balance)
print(bank.ATM_list[1].deposit(bank.user_list[1].account_list[0], 1000))
print(bank.user_list[1].name, bank.user_list[1].account_list[0].balance)
print('-------------------------')
# Deposit -1 to Hermione
print(bank.user_list[1].name, bank.user_list[1].account_list[0].balance)
print(bank.ATM_list[1].deposit(bank.user_list[1].account_list[0], -1))
print(bank.user_list[1].name, bank.user_list[1].account_list[0].balance)

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


# Test case #1 : ทดสอบ การ insert บัตร ที่เครื่อง atm เครื่องที่ 1 โดยใช้บัตร atm ของ harry
# และ Pin ที่รับมา เรียกใช้ function หรือ method จากเครื่อง ATM 
# ผลที่คาดหวัง : พิมพ์ หมายเลขบัตร ATM อย่างถูกต้อง และ หมายเลข account ของ harry อย่างถูกต้อง
# Ans : 12345, 1234567890, Success


# Test case #2 : ทดสอบฝากเงินเข้าในบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 1000 บาท
# ให้เรียกใช้ method ที่ทำการฝากเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Hermione ก่อนฝาก หลังฝาก และ แสดง transaction
# Hermione account before test : 1000
# Hermione account after test : 2000


# Test case #3 : ทดสอบฝากเงินเข้าในบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน -1 บาท
# ผลที่คาดหวัง : แสดง Error


# Test case #4 : ทดสอบการถอนเงินจากบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 500 บาท
# ให้เรียกใช้ method ที่ทำการถอนเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Hermione ก่อนถอน หลังถอน และ แสดง transaction
# Hermione account before test : 2000
# Hermione account after test : 1500


# Test case #5 : ทดสอบถอนเงินจากบัญชีของ Hermione ในเครื่อง atm เครื่องที่ 2 เป็นจำนวน 2000 บาท
# ผลที่คาดหวัง : แสดง Error

# Test case #6 : ทดสอบการโอนเงินจากบัญชีของ Harry ไปยัง Hermione จำนวน 10000 บาท ในเครื่อง atm เครื่องที่ 2
# ให้เรียกใช้ method ที่ทำการโอนเงิน
# ผลที่คาดหวัง : แสดงจำนวนเงินในบัญชีของ Harry ก่อนถอน หลังถอน และ แสดงจำนวนเงินในบัญชีของ Hermione ก่อนถอน หลังถอน แสดง transaction
# Harry account before test : 20000
# Harry account after test : 10000
# Hermione account before test : 1500
# Hermione account after test : 11500


# Test case #7 : แสดง transaction ของ Hermione ทั้งหมด 
# กำหนดให้เรียกใช้ method __str__() เพื่อใช้คำสั่งพิมพ์ข้อมูลจาก transaction ได้
# ผลที่คาดหวัง
# Hermione transaction : D-ATM:1002-1000-2000
# Hermione transaction : W-ATM:1002-500-1500
# Hermione transaction : T-ATM:1002-+10000-11500