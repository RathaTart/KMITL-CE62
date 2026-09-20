class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class CircularDoublyLinkList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            new_node.next = new_node
            new_node.prev = new_node
        else:
            tail = self.head.prev
            tail.next = new_node
            new_node.prev = tail
            new_node.next = self.head
            self.head.prev = new_node

    def prepend(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            new_node.next = new_node
            new_node.prev = new_node
        else:
            tail = self.head.prev
            new_node.prev = tail
            new_node.next = self.head
            tail.next = new_node
            self.head.prev = new_node
            self.head = new_node
    
    def display(self):
        list = []
        if self.head is None:
            print(list)
            return
        current = self.head
        while True:
            list.append(current.data)
            current = current.next
            if current == self.head:
                break
        result = '->'.join(list)
        print(result)

def find_route(cdll, source, destination, direction):
    current = cdll.head
    while current.data != source:
        current = current.next

    schedule = []
    if direction == 'F':
        while True:
            schedule.append(current.data)
            if current.data == destination:
                break
            current = current.next
    elif direction == 'B':
        while True:
            schedule.append(current.data)
            if current.data == destination:
                break
            current = current.prev

    return schedule

cdll = CircularDoublyLinkList()
print("***Railway on route***")
stations, cmds = list(map(str, input("Input Station name/Source, Destination, Direction(optional): ").split('/')))
stations = stations.split(',')
cmds = cmds.split(',')

for station in stations:
    cdll.append(station)

if len(cmds) == 3:
    source = cmds[0]
    destination = cmds[1]
    direction = cmds[2]

    if direction == 'F':
        schedule = find_route(cdll, source, destination, 'F')
        result = '->'.join(schedule)
        print('Forward Route: ' + result + ',' + str(len(schedule)-1))
    elif direction == 'B':
        schedule = find_route(cdll, source, destination, 'B')
        result = '->'.join(schedule)
        print('Backward Route: ' + result + ',' + str(len(schedule)-1))
elif len(cmds) == 2:
    source = cmds[0]
    destination = cmds[1]

    forward_schedule = find_route(cdll, source, destination, 'F')
    backward_schedule = find_route(cdll, source, destination, 'B')

    if len(forward_schedule) < len(backward_schedule):
        result = '->'.join(forward_schedule)
        print('Forward Route: ' + result + ',' + str(len(forward_schedule)-1))
    elif len(forward_schedule) > len(backward_schedule):
        result = '->'.join(backward_schedule)
        print('Backward Route: ' + result + ',' + str(len(backward_schedule)-1))
    else:
        forward_result = '->'.join(forward_schedule)
        backward_result = '->'.join(backward_schedule)
        print('Forward Route: ' + forward_result + ',' + str(len(forward_schedule)-1))
        print('Backward Route: ' + backward_result + ',' + str(len(backward_schedule)-1))
else:
    print("Invalid input format. Please provide Source, Destination, and Direction (optional).")
