def find_first_greater(arr, x):
    l, r = 0, len(arr) - 1
    result = None
    
    while l <= r:
        mid = (l + r) // 2
        if arr[mid] > x:
            result = arr[mid]
            r = mid - 1
        else:
            l = mid + 1
    
    if result is not None:
        return result
    else:
        return "No First Greater Value"

inp = input('Enter Input : ').split('/')
left, right = list(map(int, inp[0].split())), list(map(int, inp[1].split()))

left_sorted = sorted(left)

for r in right:
    print(find_first_greater(left_sorted, r))
