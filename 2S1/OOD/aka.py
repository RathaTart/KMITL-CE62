class Stack:
    def __init__(self):
        self.items = []

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        return None

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        return None

    def is_empty(self):
        return len(self.items) == 0

    def size(self):
        return len(self.items)

def count_visible_trees(heights):
    visible_count = 1
    stack = Stack()
    if len(heights) == 1:
        return 1
    if len(heights) == 0:
        return 0
    for index in range(len(heights)-1):
        if heights[index] < heights[index+1]:
            visible_count += 1
        elif heights[index] == heights[index+1]:
            continue
        else:
            break
    return visible_count


input_string = input("Enter Input : ").strip()
inputs = input_string.split(',')

heights = []
for item in inputs:
    if item.startswith('A'):
        heights.append(int(item.split()[1]))
    elif item == 'B':
        print(count_visible_trees(list(reversed(heights))))