import time
import random

# Function to perform a linear search with a sentinel
def sentinel_search(arr, target):
    arr.append(target)  # Add the sentinel
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

# Function to perform a linear search without a sentinel
def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1

# Generate a large list of random integers
size = 100000
numbers = random.sample(range(1, size + 1), size)  # Unique numbers from 1 to 100000
target = numbers[50000]  # Choosing a random target from the list

# Benchmarking the search with a sentinel
start_time = time.time()
sentinel_search(numbers.copy(), target)
sentinel_time = time.time() - start_time

# Benchmarking the search without a sentinel
start_time = time.time()
linear_search(numbers, target)
linear_time = time.time() - start_time

# Output the results
print(f"Time taken with sentinel: {sentinel_time:.6f} seconds")
print(f"Time taken without sentinel: {linear_time:.6f} seconds")
