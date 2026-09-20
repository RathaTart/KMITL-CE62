class Data:
    def __init__(self, key, value):
        self.key = key
        self.value = value

    def __str__(self):
        return "({0}, {1})".format(self.key, self.value)

class HashTable:
    def __init__(self, size, max_collision):
        self.size = size
        self.max_collision = max_collision
        self.table = [None] * size
        self.full_warning_shown = False 
    def is_full(self):
        return all(self.table)

    def hash_func(self, key):
        return sum(ord(c) for c in key) % self.size

    def insert(self, data):
        if self.is_full():
            if not self.full_warning_shown:
                print("This table is full !!!!!!")
                self.full_warning_shown = True
            return

        index = self.hash_func(data.key)
        collision_count = 0

        while self.table[index] is not None:
            collision_count += 1
            if collision_count > self.max_collision:
                print("Max of collisionChain")
                return

            print(f"collision number {collision_count} at {index}")
            index = (self.hash_func(data.key) + collision_count ** 2) % self.size

        self.table[index] = data

    def __str__(self):
        result = []
        for i in range(self.size):
            result.append(f"#{i+1}\t{self.table[i]}")
        return "\n".join(result)

print(" ***** Fun with hashing *****")
inp = input("Enter Input : ").split('/')
size, max_collision = map(int, inp[0].split())
data_list = inp[1].split(',')

hash_table = HashTable(size, max_collision)

for item in data_list:
    if hash_table.is_full():
        break

    key, value = item.split()
    data = Data(key, value)
    hash_table.insert(data)
    print(hash_table)
    print("---------------------------")
print("This table is full !!!!!!")
