def odd_even(type, data, mode):
    result = []
    if type == 'L':
        data = data.split()
        data = [item for item in data if item != ' ']
        if mode == "Even":
            for i in range (1, len(data), 2):
                result.append(data[i])
        elif mode == "Odd":
            for i in range (0, len(data), 2):
                result.append(data[i])
    elif type == 'S':
        if mode == "Even":
            for i in range (1, len(data), 2):
                result.append(data[i])
        elif mode == "Odd":
            for i in range (0, len(data), 2):
                result.append(data[i])

    return ''.join(result) if type == 'S' else result

print("*** Odd Even ***")
type, data, mode = input("Enter Input : ",).split(',')
# print("type = " + type + "| data = " + data + "| mode = " + mode)
print(odd_even(type, data, mode))
