import re

# Teststrängar
test_strings = [
    "len1: bit7",
    "len2: bit",
    "field_name: bit10"
]

pattern = r"(\w+):\s*bit(\d*)"

for test_str in test_strings:
    match = re.match(pattern, test_str)
    if match:
        variable_name = match.group(1)
        bit_length = match.group(2) if match.group(2) else 1  # Om inga bitar anges, sätt till 1
        print(f"Variable: {variable_name}, Bit length: {bit_length}")
    else:
        print(f"No match found for: {test_str}")
