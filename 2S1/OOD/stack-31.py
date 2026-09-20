class Stack():
    def __init__(self):
        self.items = []
    def push(self,i):
        self.items.append(i)
    def pop(self):
        if not self.isEmpty():
            return self.items.pop()
    def isEmpty(self):
        return self.items == []
    def size(self):
        return len(self.items)
    def __str__(self):
        return str(self.items)
    def peek(self):
        if not self.isEmpty():
            return self.items[-1]

    
input = input("Enter Input : ")
s = Stack()
count = 0
for para in input:
    if para == '[' or para == '(':
        s.push(para)
    elif para == ']':
        if s.peek() == '[':
            s.pop()
        else:
            count += 1
    elif para == ')':
        if s.peek() == '(':
            s.pop()
        else:
            count += 1
# print(s)
# print(count)
# print(s.size())
print(count+s.size())
if count == 0 and s.size() == 0:
    print("Perfect ! ! !")