def calculate_secret_code(first_ascii, last_ascii):
    return last_ascii - first_ascii
    
def generate_passwords(secret_code, ascii_list):
    generated_codes = []
    for ascii_value in ascii_list:
        generated_code = ascii_value + secret_code
        generated_codes.append(generated_code)
    return generated_codes

def translate_to_characters(ascii_list):
    translated_characters = []
    for ascii_value in ascii_list[:-2]:
        character = chr(ascii_value)
        translated_characters.append(character)
        print(translated_characters)

input_string = input("Enter code,hint : ")
char_list = list(input_string)
ascii_list = [ord(char) for char in char_list]

secret_code = calculate_secret_code(ascii_list[0], ascii_list[-1])
unlock_codes = generate_passwords(secret_code, ascii_list)
translated_characters = translate_to_characters(unlock_codes)

