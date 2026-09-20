
        return node

    def rotateLeftChild(self, root):
        new_root = root.right
        root.right = new_root.left
        new_root.left = root
        root.setHeight()
        new_root.setHeight()
        return new_root

    def rotateRightChild(self, root):
        new_root = root.left
        root.left = new_root.right
        new_root.right = root
        root.setHeight()