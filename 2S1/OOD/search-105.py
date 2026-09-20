def canPack(weights, k, maxWeight):
    box_count = 1
    current_weight = 0
    
    for weight in weights:
        if current_weight + weight > maxWeight:
            box_count += 1
            current_weight = weight
            if box_count > k:
                print("False")
                return False
        else:
            current_weight += weight
    print("True")        
    return True

def minimumWeightForBoxes(weights, k):
    left = max(weights)
    right = sum(weights) 
    
    while left < right:
        mid = (left + right) // 2
        if canPack(weights, k, mid):
            right = mid
        else:
            left = mid + 1
            
    return left

input_data = input("Enter Input : ").strip().split('/')
weights = list(map(int, input_data[0].split()))
k = int(input_data[1])

min_weight = minimumWeightForBoxes(weights, k)
print(f"Minimum weigth for {k} box(es) = {min_weight}")
