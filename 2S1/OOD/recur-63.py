first_encode = 0
first_decode = 0

def encode_char(char, rotor_position):
    if not char.isalpha():
        return char
    start = ord('A') if char.isupper() else ord('a')
    return chr((ord(char) - start + rotor_position) % 26 + start)

def decode_char(char, rotor_position):
    if not char.isalpha():
        return char
    start = ord('A') if char.isupper() else ord('a')
    return chr((ord(char) - start - rotor_position) % 26 + start)

def encode_message(message, rotor_position):
    global first_encode
    if not message:
        return ""
    rotated_char = encode_char(message[0], rotor_position)
    if rotated_char == message[0] and rotated_char != ' ' and first_encode == 0:
        rotor_position+=1
        first_encode = 1
    return encode_char(message[0], rotor_position) + encode_message(message[1:], rotor_position+1)

def decode_message(encoded_message, rotor_position):
    global first_decode
    if not encoded_message:
        return ""
    rotated_char = encode_char(message[0], rotor_position)
    if rotated_char == message[0] and rotated_char != ' ' and first_decode == 0:
        rotor_position+=1
        first_decode = 1
    return decode_char(encoded_message[0], rotor_position) + decode_message(encoded_message[1:], rotor_position+1)


print("This is Caesar cipher")
message, initial_rotor_position = input("Enter Input : ").split(',')
initial_rotor_position = int(initial_rotor_position) % 26
encoded = encode_message(message, initial_rotor_position)
print("Encoded Message:", encoded)
decoded = decode_message(encoded, initial_rotor_position)
print("Decoded Message:", decoded)
