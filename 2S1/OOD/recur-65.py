def staircase(n, row=0):
    if n == 0:
        print("Not Draw!")
        return
    if row == n or row == -n:
        return 
    if n>0:
        print("_" * (n-row-1) + "#" * (row+1))
        staircase(n, row+1)
    elif n<0:
        print("_" * (row) + "#" * (-n-row))
        staircase(n, row+1)

staircase(int(input("Enter Input : ")))