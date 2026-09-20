class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class LinkList:
    def __init__(self):
        self.head = None
    
    def append(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return
        run = self.head
        while run.next:
            run = run.next
        run.next = new_node

    def prepend(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
            return
        new_node.next = self.head
        self.head = new_node

    def delete(self, data):
        if self.head is None:
            return
        if self.head.data == data:
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
            if run.data == data:
                return True
            run = run.next
        return False
    
    def display(self):
        list_data = []
        run = self.head
        while run:
            list_data.append(run.data)
            run = run.next
        return list_data
    
    def reverse(self):
        prev = None
        current = self.head 
        while current:
            next_node = current.next
            current.next = prev
            prev = current
            current = next_node
        self.head = prev

def merge_lists(list1, list2):
    merged_list = LinkList()
    current = list1.head
    while current:
        merged_list.append(current.data)
        current = current.next
    current = list2.head
    while current:
        merged_list.append(current.data)
        current = current.next
    return merged_list

# Input
L1, L2 = input("Enter Input (L1,L2) : ").split()
L1 = L1.split('->')
L2 = L2.split('->')

ll1 = LinkList()
ll2 = LinkList()

for item in L1:
    ll1.append(item)
for item in L2:
    ll2.append(item)


ll2.reverse()

merged_list = merge_lists(ll1, ll2)


print("L1    :", ' '.join(L1))
print("L2    :", ' '.join(L2))
print("Merge :", ' '.join(merged_list.display()))
