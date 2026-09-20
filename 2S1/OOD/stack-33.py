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


def postFixeval(st):
    s = Stack()
    for num in st:
        if num == '+':
            int1 = s.pop()
            int2 = s.pop()
            result = int2 + int1
            s.push(result)
        elif num == '-':
            int1 = s.pop()
            int2 = s.pop()
            result = int2 - int1
            s.push(result)
        elif num == '*':
            int1 = s.pop()
            int2 = s.pop()
            result = int2 * int1
            s.push(result)
        elif num == '/':
            int1 = s.pop()
            int2 = s.pop()
            result = int2 / int1
            s.push(result)
        else:
            s.push(float(num))
    return s.pop()

            


print(" ***Postfix expression calcuation***")

token = list(input("Enter Postfix expression : ").split())



print("Answer : ","{:.2f}".format(postFixeval(token)))

