class Node:
    def __init__(self, data):
        self.data = int(data)
        self.left = None
        self.right = None
    
    def __str__(self):
        return str(self.data)

class BST:
    def __init__(self):
        self.root = None

    def insert(self, data):
        if self.root is None:
            self.root = Node(data)
        else:
            cur = self.root
            while True:
                if data < cur.data and cur.left is not None:
                    cur = cur.left
                elif data >= cur.data and cur.right is not None:
                    cur = cur.right
                elif data < cur.data:
                    cur.left = Node(data)
                    break
                else:
                    cur.right = Node(data)
                    break
        return self.root
    
    def preorder(self, node):
        if node is None:
            return []
        return [node.data] + self.preorder(node.left) + self.preorder(node.right)

    def inorder(self, node):
        if node is None:
            return []
        return self.inorder(node.left) + [node.data] + self.inorder(node.right)

    def postorder(self, node):
        if node is None:
            return []
        return self.postorder(node.left) + self.postorder(node.right) + [node.data]

    def breadth(self):
        if self.root is None:
            return []
        queue = [self.root]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node.data)
            if node.left is not None:
                queue.append(node.left)
            if node.right is not None:
                queue.append(node.right)
        return result
    
    def print_str(self, traversal_name, traversal_result):
        print(f"{traversal_name} : {' '.join(map(str, traversal_result))}")

# Convert the input to integers
input_data = list(map(int, input("Enter Input : ").split()))

t = BST()
for data in input_data:
    t.insert(data)

t.print_str("Preorder", t.preorder(t.root))
t.print_str("Inorder", t.inorder(t.root))
t.print_str("Postorder", t.postorder(t.root))
t.print_str("Breadth", t.breadth())
