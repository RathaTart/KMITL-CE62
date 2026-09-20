class Stack():
    def __init__(self):
        self.items = []
    def push(self, i):
        self.items.append(int(i))
    def pop(self):
        if not self.isEmpty():
            return self.items.pop()
        else:
            return -1
    def delete(self, num):
        deleted_items = [item for item in self.items if item == num]
        self.items = [item for item in self.items if item != num]
        return deleted_items if deleted_items else -1
    def isEmpty(self):
        return self.items == []
    def size(self):
        return len(self.items)
    def __str__(self):
        return str(self.items)
    def peek(self):
        if not self.isEmpty():
            return self.items[-1]

def ManageStack(commands):
    s = Stack()
    for cmd in commands:
        if cmd[0] == 'A':
            _, num = cmd.split()
            print("Add =", num)
            s.push(int(num))
        elif cmd[0] == 'P':
            if s.isEmpty():
                print('-1')
            else:
                pop = s.pop()
                print("Pop =", pop)
        elif cmd[0] == 'D':
            _, num = cmd.split()
            if s.isEmpty():
                print('-1')
            else:
                deletes = s.delete(int(num))
                if deletes == -1:
                    pass
                else:
                    for delete in deletes: 
                        print("Delete =", delete)
        elif cmd[0] == 'L':
            _, num = cmd.split()
            if s.isEmpty():
                print('-1')
            else:
                temp_stack = Stack()
                num = int(num)
                deleted_items = []
                while not s.isEmpty():
                    item = s.pop()
                    if item >= num:
                        temp_stack.push(item)
                    else:
                        deleted_items.append(item)
                while not temp_stack.isEmpty():
                    s.push(temp_stack.pop())
                if deleted_items:
                    for item in deleted_items:
                        print("Delete =", item, "Because", item,"is less than", num)
        elif cmd[0] == 'M':
            _, num = cmd.split()
            if s.isEmpty():
                print('-1')
            else:
                temp_stack = Stack()
                num = int(num)
                deleted_items = []
                while not s.isEmpty():
                    item = s.pop()
                    if item <= num:
                        temp_stack.push(item)
                    else:
                        deleted_items.append(item)
                while not temp_stack.isEmpty():
                    s.push(temp_stack.pop())
                if deleted_items:
                    for item in deleted_items:
                        print("Delete =", item, "Because", item,"is more than", num)

    # Display remaining items in the stack
    print("Value in Stack =", s)

# Example usage
input_commands = input("Enter Input : ").split(',')
ManageStack(input_commands)
