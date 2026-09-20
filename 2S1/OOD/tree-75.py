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
        new_node = Node(data)
        if self.root is None:
            self.root = new_node
        else:
            current = self.root
            while True:
                if data < current.data:
                    if current.left is None:
                        current.left = new_node
                        break
                    current = current.left
                else:
                    if current.right is None:
                        current.right = new_node
                        break
                    current = current.right
        return self.root

    def find_min(self, node):
        current = node
        while current.left is not None:
            current = current.left
        return current

    def delete(self, root, data):
        if root is None:
            print("Error! Not Found DATA")
            return root
        if data < root.data:
            root.left = self.delete(root.left, data)
        elif data > root.data:
            root.right = self.delete(root.right, data)
        else:
            if root.left is None:
                return root.right
            elif root.right is None:
                return root.left
            root.data = self.find_min(root.right).data
            root.right = self.delete(root.right, root.data)
        return root
    
    def printTree(self, node, level=0):
        if node is not None:
            self.printTree(node.right, level + 1)
            print('     ' * level, node)
            self.printTree(node.left, level + 1)

    def removeless(self, node, data, path=None, count=None, removed_flag=[False]):
        if path is None:
            path = []
        if count is None:
            count = [1]
        if node is None:
            return None

        path.append(node.data)

        # First, recursively process the left and right children
        node.left = self.removeless(node.left, data, path.copy(), count, removed_flag)
        node.right = self.removeless(node.right, data, path.copy(), count, removed_flag)

        # Calculate the sum of the current path
        sumval = sum(path)

        # If both left and right children are None, check if this node should be removed
        if node.left is None and node.right is None and sumval < data:
            print(f"{count[0]}) {'->'.join(map(str, path))} = {sumval}")
            count[0] += 1
            removed_flag[0] = True
            return None

        return node

    def removegreater(self, node, data, path=None, count=None, removed_flag=[False]):
        if path is None:
            path = []
        if count is None:
            count = [1]

        if node is None:
            return None

        path.append(node.data)
        sumval = sum(path)
        
        node.left = self.removegreater(node.left, data, path.copy(), count, removed_flag)
        node.right = self.removegreater(node.right, data, path.copy(), count, removed_flag)

        if node.left is None and node.right is None and sumval > data:
            print(f"{count[0]}) {'->'.join(map(str, path))} = {sumval}")
            count[0] += 1
            removed_flag[0] = True
            return None

        return node

    def removeequal(self, node, data, path=None, count=None, removed_flag=[False]):
        if path is None:
            path = []
        if count is None:
            count = [1]
        if node is None:
            return None

        path.append(node.data)
        sumval = sum(path)

        if node.left is None and node.right is None and sumval == data:
            print(f"{count[0]}) {'->'.join(map(str, path))} = {sumval}")
            count[0] += 1
            removed_flag[0] = True
            return None
        
        node.left = self.removeequal(node.left, data, path.copy(), count, removed_flag)
        node.right = self.removeequal(node.right, data, path.copy(), count, removed_flag)

        return node

    def is_fallen(self, root):
        return root is None

def parse_input(input_str):
    commands = input_str.strip().split(',')
    return commands

# --- Simulation Starts Here ---

tree = BST()
input_str = input("Enter <Create City A (BST)>/<Create conditions and deploy the army>: ")
input_str = input_str.split('/')

# Create City A (BST)
commands = parse_input(input_str[1])
for i in input_str[0].split():
    root = tree.insert(int(i))

# Print City A before the war
print("(City A) Before the war:")
tree.printTree(root)

# Deploy the army and process the commands
for command in commands:
    if command[0] == 'L':
        print("--------------------------------------------------")
        print(f"Removing paths where the sum is less than {int(command[2:])}:") 
        removed_flag = [False]
        root = tree.removeless(root, int(command[2:]), [], [1], removed_flag)
        if not removed_flag[0]:
            print("No paths were removed.")
    elif command[0] == 'M':
        print("--------------------------------------------------")
        print(f"Removing paths where the sum is greater than {int(command[2:])}:") 
        removed_flag = [False]
        root = tree.removegreater(root, int(command[2:]), [], [1], removed_flag)
        if not removed_flag[0]:
            print("No paths were removed.")
    elif command[0] == 'E':
        print("--------------------------------------------------")
        print(f"Removing paths where the sum is equal to {int(command[3:])}:") 
        removed_flag = [False]
        root = tree.removeequal(root, int(command[3:]), [], [1], removed_flag)
        if not removed_flag[0]:
            print("No paths were removed.")
    
    if tree.is_fallen(root):
        print("--------------------------------------------------")
        print("(City A) After the war:")
        print("City A has fallen!")
        break

    print("--------------------------------------------------")
    print("(City A) After the war:")
    tree.printTree(root)
