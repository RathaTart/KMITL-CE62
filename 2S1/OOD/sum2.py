def sum_to_five(input):
    result = []
    array = sorted(input)
    if len(array)>2:
        for i in range(len(array)):
            for j in range(len(array)):
                for k in range(len(array)):
                    if i != j and i != k and j != k and i<j and j<k:
                        if int(array[i]) + int(array[j]) + int(array[k]) == 5:
                            if [int(array[i]), int(array[j]), int(array[k])] not in result:
                                result.append([int(array[i]), int(array[j]), int(array[k])])
        
        return result
    else:
        return "Array Input Length Must More Than 2"

array = map(int, input("Enter Your List : ").split())
print(sum_to_five(array))