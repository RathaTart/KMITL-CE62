def rearrange_non_negatives(nums):
    non_negatives = [num for num in nums if num >= 0]
    
    for i in range(len(non_negatives)):
        for j in range(i + 1, len(non_negatives)):
            if non_negatives[i] > non_negatives[j]:
                non_negatives[i], non_negatives[j] = non_negatives[j], non_negatives[i]

    non_neg_idx = 0
    for i in range(len(nums)):
        if nums[i] >= 0:
            nums[i] = non_negatives[non_neg_idx]
            non_neg_idx += 1

    return nums



input_data = input("Enter Input : ").split()
nums = list(map(int, input_data))

result = rearrange_non_negatives(nums)
print(" ".join(map(str, result)))
