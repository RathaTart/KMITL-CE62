class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if self.head == None:
            self.head = new_node
            return
        run = self.head
        while run.next:
            run = run.next
        run.next = new_node


    def prepend(self, data):
        new_node = Node(data)
        if self.head == None:
            self.head = new_node
            return
        new_node.next = self.head
        self.head = new_node
        

    def delete(self, data):
        if self.head == None:
            return
        if self.head == data:
            self.head = self.head.next
            return
        run = self.head
        while run.next:
            if run.next.data == data:
                run.next = run.next.next
                return
            run = run.next
            
    def find(self, data):
        run = self.head
        while run:
            if run == data:
                return True
            run = run.next
        return False
    
    def display(self):
        list = []
        run = self.head
        while run:
            list.append(run.data)
            run = run.next
        return list


ll = LinkList()
datas = list(map(int, input("Enter the numbers list: ").split()))

for data in datas:
    if data % 2 == 0:
        ll.append(data)
for data in datas:
    if data % 2 == 1:
        ll.append(data)

print("Rearranged list:",ll.display())