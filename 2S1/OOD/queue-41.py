class Queue:
    def __init__(self):
        self.items = []
    
    def enqueue(self, value):
        self.items.append(value)
        return f"Add {value} index is {len(self.items) - 1}"
    
    def dequeue(self):
        if self.is_empty():
            return -1
        else:
            removed_value = self.items.pop(0)
            return f"Pop {removed_value} size in queue is {len(self.items)}"
    
    def is_empty(self):
        return len(self.items) == 0
    
    def __str__(self):
        if self.is_empty():
            return "Empty"
        else:
            return "Number in Queue is :  " + str(self.items)


queue = Queue()
input_data = input("Enter Input : ").split(",")

for command in input_data:
    if command.startswith('E'):
        value = command.split()[1]
        print(queue.enqueue(value))
    elif command == 'D':
        print(queue.dequeue())

print(queue)


