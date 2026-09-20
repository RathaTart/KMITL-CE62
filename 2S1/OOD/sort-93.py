def check_ascending(lst):
    for i in range(len(lst) - 1):
        if lst[i] > lst[i + 1]:
            return False
    return True

def check_descending(lst):
    for i in range(len(lst) - 1):
        if lst[i] < lst[i + 1]:
            return False
    return True

def check_duplicates(lst):
    for i in range(len(lst)):
        for j in range(i + 1, len(lst)):
            if lst[i] == lst[j]:
                return True
    return False

def ckeck_all_same(lst):
    first = lst[0]
    for num in lst:
        if num != first:
            return False
    return True

def classify_number(n):
    num_str = str(n)
    digits = [int(digit) for digit in num_str]
    
    if ckeck_all_same(digits):
        return "Repdrome"
    elif check_ascending(digits):
        if check_duplicates(digits):
            return "Plaindrome"
        else:
            return "Metadrome"
    elif check_descending(digits):
        if check_duplicates(digits):
            return "Nialpdrome"
        else:
            return "Katadrome"
    else:
        return "Nondrome"


input_data = int(input("Enter Input : "))
result = classify_number(input_data)
print(result)
