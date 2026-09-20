class QueueSimulation:
    def __init__(self, people):
        self.main_queue = list(people)
        self.cashier1_queue = []
        self.cashier2_queue = []
        self.minutes_passed = 0
        self.first1 = 0
        self.first2 = 0
    
    def simulate(self):
        while self.main_queue:

            if self.cashier1_queue:
                self.minutes_cashier1 += 1
                if self.minutes_cashier1 % 3 == 0 and self.minutes_cashier1 != 0:
                    self.cashier1_queue.pop(0)
            if self.cashier2_queue:
                self.minutes_cashier2 += 1
                if self.minutes_cashier2 % 2 == 0 and self.minutes_cashier2 != 0:
                    self.cashier2_queue.pop(0)

            if self.main_queue:
                customer = self.main_queue.pop(0)
                if len(self.cashier1_queue) < 5:
                    self.cashier1_queue.append(customer)
                    if self.first1 == 0:
                        self.minutes_cashier1 = 0
                        self.first1 = 1
                elif len(self.cashier2_queue) < 5:
                    self.cashier2_queue.append(customer)
                    if self.first2 == 0:
                        self.minutes_cashier2 = 0
                        self.first2 = 1

            self.minutes_passed += 1

            print(f"{self.minutes_passed} {self.main_queue} {self.cashier1_queue} {self.cashier2_queue}")


input_people = input("Enter people : ").strip()
simulation = QueueSimulation(input_people)
simulation.simulate()

