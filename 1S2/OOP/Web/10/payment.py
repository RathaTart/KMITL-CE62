class Payment :
    def __init__(self, amount, method):
        self.amount = amount
        self.method = method
    
    def pay(self):
        return 1