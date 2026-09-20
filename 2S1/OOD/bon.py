def bon(str):
	my_dict = {}
	str = ''.join(sorted(str))
	count = 1
	for i in range(0, len(str)):
		if str[i-1] == str[i]:
			count+=1
			my_dict[str[i]] = count
		else:
			count = 1
			my_dict[str[i]] = count
	
	max_value = max(my_dict.values())
	max_key = [key for key, value in my_dict.items() if value == max_value][0]
	result = ord(max_key)-ord('a')+1	
	
	return result*4

secretCode = input("Enter secret code : ")
print(bon(secretCode))