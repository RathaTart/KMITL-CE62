class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None
    
    def __str__(self):
        return str(self.data)

class BST:
    def __init__(self):
        self.root = None

    def insert(self, data):
        if self.root == None:
            self.root = Node(data)
        else:
            cur = self.root
            while True:
                if data < cur.data and cur.left != None:
                    cur = cur.left
                elif data >= cur.data and cur.right != None:
                    cur = cur.right
                elif data < cur.data:
                    cur.left = Node(data)
                    break
                else:
                    cur.right = Node(data)
                    break
        return self.root
    
    def search(self, data):
        cur = self.root
        while cur is not None:
            if data == cur.data:
                return self.printSearch(cur)
            elif data < cur.data:
                cur = cur.left
            elif data >= cur.data:
                cur = cur.right
        return []

    def printSearch(self, node):
        if node is None:
            return []
        result = []
        stack = [node]
        while stack:
            current = stack.pop()
            result.append(current.data)
            # print(f"left = {current.left} , right = {current.right}")
            if current.right:
                stack.append(current.right)
            if current.left:
                stack.append(current.left)
            # print("result = ", result)
        return result

            
T = BST()
inp, val = input('Enter the BST values and search value: ').split(',')
inp = inp.split()
inp = [int(i) for i in inp]
val = int(val)
print(f"Input: root = {inp}, val = {val}")

for i in inp:
    T.insert(i)

print(f"Output: {T.search(val)}")

