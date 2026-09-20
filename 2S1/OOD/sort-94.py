def insert_sorted(arr, num):
    if len(arr) == 0:
        arr.append(num)
    else:
        inserted = False
        for i in range(len(arr)):
            if num < arr[i]:
                arr.insert(i, num)
                inserted = True
                break
        if not inserted:
            arr.append(num)

def find_median(arr):
    n = len(arr)
    if n % 2 == 1:
        return arr[n // 2]
    else:
        return (arr[n // 2] + arr[n // 2 - 1]) / 2


input_nums = input("Enter Input : ").split()

if input_nums[0] == 'EX':
    Ans = "merge sort"
    print("Extra Question : What is a suitable sort algorithm?")
    print("   Your Answer : " + Ans)
else:
    input_nums = list(map(int, input_nums))
    sorted_list = []

    for i in range(len(input_nums)):
        insert_sorted(sorted_list, input_nums[i]) 
        median = find_median(sorted_list) 
        print(f"list = {input_nums[:i+1]} : median = {median:.1f}")

