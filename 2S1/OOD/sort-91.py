def check_sort(arr):  
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return 'No'
    return 'Yes'

print(check_sort(list(map(int, (input('Enter Input : ').split())))))

