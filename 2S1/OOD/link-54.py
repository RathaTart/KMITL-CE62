class Node:
    def __init__(self, value=None, next=None):
        self.value = value
        self.next = next

class LinkList:
    def __init__(self):
        self.head = None

    def appendHead(self, value):
        node = Node(value, self.head)
        self.head = node

    def appendLast(self, value):
        if self.head is None:
            self.appendHead(value)
            return
        run = self.head
        while run.next:
            run = run.next
        run.next = Node(value)

    def removeLast(self):
        if self.head is None:
            print("Error!!!")
            return
        if self.head.next is None:
            self.head = None
            return
        run = self.head
        while run.next.next:
            run = run.next
        run.next = None

    def rename(self, newName):
        if self.head is None:
            print("Error!!!")
            return
        run = self.head
        while run.next:
            run = run.next
        run.value = newName

    def printList(self):
        if self.head is None:
            print("Linklist is empty!")
            return
        run = self.head
        result = []
        while run:
            result.append(run.value)
            run = run.next
        print(' -> '.join(result))

    def printListWithNoDuplicate(self):
        if self.head is None:
            print("Linklist is empty!")
            return
        seen = set()
        run = self.head
        result = []
        while run:
            if run.value not in seen:
                result.append(run.value)
                seen.add(run.value)
            run = run.next
        print(' -> '.join(result))

def convertToLinkList(ls):
    linked_list = LinkList()
    for item in ls:
        linked_list.appendLast(item)
    return linked_list

print("*** My Favourite Keynote ***")
inputl = input("Enter Input / List of operation : ").split('/')
listSong = [ele for ele in inputl[0].strip().split(' ')]
operations = [ele for ele in inputl[1].strip().split(", ")]

myLinkList = convertToLinkList(listSong)
myLinkList.printList()

for op in operations:
    if op[0] == 'A':
        _, value = op.split(' ')
        myLinkList.appendLast(value)
    elif op[0] == 'D':
        myLinkList.removeLast()
    elif op[0] == 'R':
        _, newName = op.split(' ')
        myLinkList.rename(newName)

myLinkList.printList()
myLinkList.printListWithNoDuplicate()
