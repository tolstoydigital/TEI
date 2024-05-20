class NumberUtils:

    
    @staticmethod
    def convert_roman_numeral_to_number(s: str) -> int:
        roman_values = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

        int_val = 0

        for i in range(len(s)):
            if i > 0 and roman_values[s[i]] > roman_values[s[i - 1]]:
                int_val += roman_values[s[i]] - 2 * roman_values[s[i - 1]]
            else:
                int_val += roman_values[s[i]]
        
        return int_val