class Node:
    def __init__(self, data, left=None, right=None):
        self.data = data
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return f"Node({self.data})"

    def height(self):
        return (max(self.left.height() if self.left else -1,
                    self.right.height() if self.right else -1) + 1)

    def balance(self):
        return (self.left.height() if self.left else -1) - (self.right.height() if self.right else -1)

    @staticmethod
    def leftRotate(x):
        x_new = x.right
        x.right = x_new.left
        x_new.left = x
        return x_new

    @staticmethod
    def rightRotate(y):
        y_new = y.left
        y.left = y_new.right
        y_new.right = y
        return y_new

    def insert(root, data):
        if root is None:
            return Node(data)
        branch = "left" if data < root.data else "right"
        root.__dict__[branch] = Node.insert(root.__dict__[branch], data)

        balance = Node.balance(root)
        if balance > 1: 
            if Node.balance(root.left) < 0: 
                root.left = Node.leftRotate(root.left)
            return Node.rightRotate(root)
        elif balance < -1: 
            if Node.balance(root.right) > 0: 
                root.right = Node.rightRotate(root.right)
            return Node.leftRotate(root)

        return root

    def _gen_display(self) -> 'tuple[list, int, int, int]':
        '''
        return
        - tree image: list[str]
        - left spacing: int
        - value width: int
        - right spacing: int
        '''
        if self is None:
            return [], 0, 0, 0
        lt, lf, lv, lb = Node._gen_display(self.left)
        rt, rf, rv, rb = Node._gen_display(self.right)
        data = str(self.data)
        if not lt and not rt:
            return [data], 0, len(data), 0
        add_left, add_right = int(bool(lt)), int(bool(rt))
        line = ((' '*(lf+lv) + '/' + ' '*(lb)) * add_left +
                ' ' * len(data) +
                (' '*rf + '\\' + ' '*(rv+rb)) * add_right)
        out = [' '*(lf+lv+add_left) + '_'*lb + data +
               '_'*rf + ' '*(rv+rb+add_right), line]
        if len(lt) > len(rt):
            rt.extend([' ' * (rf+rv+rb)] * (len(lt) - len(rt)))
        elif len(lt) < len(rt):
            lt.extend([' ' * (lf+lv+lb)] * (len(rt) - len(lt)))
        for l, r in zip(lt, rt):
            out.append(l + ' '*(len(data)+add_left+add_right) + r)
        return out, (lf+lv+lb+add_left), len(data), (rf+rv+rb+add_right)

    
    @staticmethod
    def parentOf(root, data) -> 'tuple[Node, str]':
        if root is None:
            return None, ""
        if root.data == data:
            return Node(None, left=root), "left"
        direction = "left" if data < root.data else "right"
        child = root.left if direction == "left" else root.right
        if child is None:
            return None, ""
        if child.data == data:
            return root, direction
        return Node.parentOf(child, data)

rotate, direction, inp = input('Enter input: ').split(',')
rotate = int(rotate)
root = None
for i in map(int, inp.split()):
    root = Node.insert(root, i)
tree_image = root._gen_display()
print("Before")
print(*tree_image[0], sep='\n')
# print(tree_image)
print("-" * sum(tree_image[1:]))

parent, branch = Node.parentOf(root, rotate)
print(parent)
print(branch)
if parent is None:
    print(f"No {rotate} in this tree")
    exit()
root_parent = Node(None, root) if parent.data else parent

rotate_func = {'left': Node.leftRotate, 'right': Node.rightRotate}
other_dir = 'right' if direction == 'left' else 'left'

cur = parent
while cur:
    while getattr(cur, branch) and getattr(getattr(cur, branch), other_dir):
        setattr(cur, branch, rotate_func[direction](getattr(cur, branch)))
    cur = getattr(cur, branch)
    branch = direction

tree_image = root_parent.left._gen_display()
print("After")
print(*tree_image[0], sep='\n')