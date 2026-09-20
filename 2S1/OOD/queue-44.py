class Queue:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def enqueue(self, item):
        self.items.append(item)

    def dequeue(self):
        if not self.is_empty():
            return self.items.pop(0)
        else:
            return None

    def size(self):
        return len(self.items)

    def __str__(self):
        if self.is_empty():
            return "Empty"
        else:
            return ", ".join(f"{item[0]}:{item[1]}" for item in self.items)

class QueueSimulation:
    def __init__(self, input_data):
        self.my_queue = Queue()
        self.your_queue = Queue()
        self.my_activities = {}
        self.your_activities = {}
        self.score = 0
        
        self.parse_input(input_data)
    
    def parse_input(self, input_data):
        days_data = input_data.split(',')
        for day_data in days_data:
            if ':' in day_data:
                my_data, your_data = day_data.split()
                my_activity, my_location = my_data.split(':')
                your_activity, your_location = your_data.split(':')
                
                self.my_queue.enqueue((my_activity, my_location))
                self.your_queue.enqueue((your_activity, your_location))
                
                if my_activity in self.my_activities:
                    self.my_activities[my_activity].append(my_location)
                else:
                    self.my_activities[my_activity] = [my_location]
                
                if your_activity in self.your_activities:
                    self.your_activities[your_activity].append(your_location)
                else:
                    self.your_activities[your_activity] = [your_location]
    
    def calculate_score(self):
        while not self.my_queue.is_empty() and not self.your_queue.is_empty():
            my_act, my_loc = self.my_queue.dequeue()
            your_act, your_loc = self.your_queue.dequeue()
            
            if my_act == your_act and my_loc == your_loc:
                self.score += 4
            elif my_act == your_act:
                self.score += 1
            elif my_loc == your_loc:
                self.score += 2
            else:
                self.score -= 5
        
        if self.score >= 7:
            return "Yes! You're my love! : Score is {}.".format(self.score)
        elif 1 <= self.score <= 6:
            return "Umm.. It's complicated relationship! : Score is {}.".format(self.score)
        else:
            return "No! We're just friends. : Score is {}.".format(self.score)
    
    def display_queues(self):
        my_queue_str = str(self.my_queue)
        your_queue_str = str(self.your_queue)
        
        activity_names = {
            '0': 'Eat',
            '1': 'Game',
            '2': 'Learn',
            '3': 'Movie'
        }
        
        location_names = {
            '0': 'Res.',
            '1': 'ClassR.',
            '2': 'SuperM.',
            '3': 'Home'
        }
        
        my_activities_str = ", ".join(f"{activity_names[act[0]]}:{location_names[act[1]]}" for act in self.my_queue.items)
        your_activities_str = ", ".join(f"{activity_names[act[0]]}:{location_names[act[1]]}" for act in self.your_queue.items)
        
        print(f"My   Queue = {my_queue_str}")
        print(f"Your Queue = {your_queue_str}")
        print(f"My   Activity:Location = {my_activities_str}")
        print(f"Your Activity:Location = {your_activities_str}")




input_data = input("Enter Input : ").strip()
simulation = QueueSimulation(input_data)
simulation.display_queues()
result = simulation.calculate_score()
print(result)


