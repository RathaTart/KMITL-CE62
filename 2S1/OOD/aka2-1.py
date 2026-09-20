class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0
        
    def push(self, data):
        self.items.append(data)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        else:
            return None
        
    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        else:
            return None
    
    def size(self):
        return len(self.items)
    
    def __str__(self):
        return str(self.items)
    
def count_visible_trees(stack):
    if stack.is_empty():
        return 0
    visible_count = 0
    max_height = 0
    temp_stack = Stack()

    while not stack.is_empty():
        height = stack.pop()
        temp_stack.push(height)
        if height > max_height:
            visible_count += 1
            max_height = height
    
    while not temp_stack.is_empty():
        stack.push(temp_stack.pop())
    
    return visible_count

def handle_poison_effect(stack):
    temp_stack = Stack()
    while not stack.is_empty():
        height = stack.pop()
        if height % 2 == 1:
            height += 2
        else:
            height -= 1
        temp_stack.push(height)
    
    while not temp_stack.is_empty():
        stack.push(temp_stack.pop())

def main():
    input_data = input("Enter Input : ").split(",")

    stack = Stack()

    for command in input_data:
        if command.startswith('A'):
            height = int(command.split()[1])
            stack.push(height)
        elif command == 'B':
            print(count_visible_trees(stack))
        elif command == 'S':
            handle_poison_effect(stack)

if __name__ == "__main__":
    main()
