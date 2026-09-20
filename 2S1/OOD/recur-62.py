def palindrome(n):
    if n != [] and len(n) >= 2:
        if n[0] == n[-1]:

            return palindrome(n[1:-1])
        elif len(n) == 0 or len(n) == 1:
            return True
        else:
            return False
    return True

data = input("Enter Input : ")
result = palindrome(data)
if result == True:
    print(f"\'{data}' is palindrome")
elif result == False:
    print(f"\'{data}' is not palindrome")