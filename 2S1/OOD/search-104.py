class HashTable:
    def __init__(self, table_size, max_collisions, load_threshold):
        self.table_size = table_size
        self.max_collisions = max_collisions
        self.load_threshold = load_threshold
        self.table = [None] * table_size
        self.data_count = 0
        self.stored_keys = set()

    def insert_key(self, key):
        index = key % self.table_size
        original_index = index
        collision_count = 0

        while collision_count < self.max_collisions:
            if self.table[index] is None:
                self.table[index] = key
                self.data_count += 1
                self.stored_keys.add(key)
                return True
            else:
                collision_count += 1
                print(f"collision number {collision_count} at {index}")
                if collision_count >= self.max_collisions:
                    print("****** Max collision - Rehash !!! ******")
                    return False
                index = (original_index + collision_count ** 2) % self.table_size
        return False

    def needs_rehash(self):
        current_load_percentage = (self.data_count + 1) / self.table_size * 100
        if current_load_percentage >= self.load_threshold:
            print("****** Data over threshold - Rehash !!! ******")
            return True
        return False

    def rehash_table(self):
        new_table_size = self.get_next_prime(self.table_size * 2)
        self.table_size = new_table_size
        self.table = [None] * self.table_size
        self.data_count = 0
        for key in self.stored_keys:
            self.insert_key(key)

    def get_next_prime(self, number):
        def is_prime(num):
            if num <= 1:
                return False
            if num <= 3:
                return True
            if num % 2 == 0 or num % 3 == 0:
                return False
            i = 5
            while i * i <= num:
                if num % i == 0 or num % (i + 2) == 0:
                    return False
                i += 6
            return True

        next_prime = number
        while not is_prime(next_prime):
            next_prime += 1
        return next_prime

    def display_table(self):
        for i, value in enumerate(self.table):
            print(f"#{i + 1}\t{value if value is not None else 'None'}")
        print("----------------------------------------")

    def add_key(self, key):
        print(f"Add : {key}")
        if self.needs_rehash():
            self.rehash_table()

        success = self.insert_key(key)
        if not success:
            self.rehash_table()
            self.insert_key(key)
        
        self.display_table()


print(" ***** Rehashing *****")
user_input = input("Enter Input : ").split('/')
table_params = list(map(int, user_input[0].split()))
table_size, max_collisions, threshold = table_params
keys_to_add = list(map(int, user_input[1].split()))

hash_table = HashTable(table_size, max_collisions, threshold)
print("Initial Table :")
hash_table.display_table()

for key in keys_to_add:
    hash_table.add_key(key)
