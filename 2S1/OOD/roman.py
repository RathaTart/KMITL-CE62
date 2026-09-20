class translator:

    def deciToRoman(self, num):
        if not isinstance(num, int) or not 1 <= num <= 3999:
            return "Invalid number: Enter a number between 1 and 3999."

        roman_numerals = {
            1000: 'M', 900: 'CM', 500: 'D', 400: 'CD',
            100: 'C', 90: 'XC', 50: 'L', 40: 'XL',
            10: 'X', 9: 'IX', 5: 'V', 4: 'IV',
            1: 'I'
        }

        roman = ''
        for value, numeral in roman_numerals.items():
            while num >= value:
                roman += numeral
                num -= value

        return roman

    def romanToDeci(self, s):
        roman_numerals = {
            'M': 1000, 'CM': 900, 'D': 500, 'CD': 400,
            'C': 100, 'XC': 90, 'L': 50, 'XL': 40,
            'X': 10, 'IX': 9, 'V': 5, 'IV': 4,
            'I': 1
        }

        decimal = 0
        prev_value = 0

        for char in s:
            current_value = roman_numerals[char]
            if current_value > prev_value:
                decimal += current_value - 2 * prev_value
            else:
                decimal += current_value
            prev_value = current_value

        return decimal


num = int(input("Enter number to translate : "))
translator_instance = translator()

roman_numeral = translator_instance.deciToRoman(num)
print(roman_numeral)

decimal_value = translator_instance.romanToDeci(roman_numeral)
print(decimal_value)
