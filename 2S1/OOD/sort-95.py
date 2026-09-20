def find_subsets_with_sum(numbers, target_sum):
    results = []
    
    def backtrack(start, path, current_sum):
        if current_sum == target_sum:
            results.append(path[:])
            return
        for i in range(start, len(numbers)):
            if i > start and numbers[i] == numbers[i - 1]:
                continue
            if current_sum + numbers[i] > target_sum:
                continue 
            path.append(numbers[i])
            backtrack(i + 1, path, current_sum + numbers[i])
            path.pop()
    
    numbers.sort()
    backtrack(0, [], 0)
    return results

def custom_sort(arrays):
    def compare(a, b):
        if len(a) < len(b):
            return -1
        elif len(a) > len(b):
            return 1
        else:
            for i in range(len(a)):
                if a[i] < b[i]:
                    return -1
                elif a[i] > b[i]:
                    return 1
            return 0
    
    def insertion_sort(arrays):
        for i in range(1, len(arrays)):
            key = arrays[i]
            j = i - 1
            while j >= 0 and compare(arrays[j], key) > 0:
                arrays[j + 1] = arrays[j]
                j -= 1
            arrays[j + 1] = key
    
    insertion_sort(arrays)
    return arrays


input_str = input("Enter Input : ")
target_str, numbers_str = input_str.split('/')
target_sum = int(target_str)
numbers = list(map(int, numbers_str.split()))

subsets = find_subsets_with_sum(numbers, target_sum)

if not subsets:
    print("No Subset")
else:
    sorted_subsets = custom_sort(subsets)
    for subset in sorted_subsets:
        print(subset)

