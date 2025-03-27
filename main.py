#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import re
import sys


"""

TODO: Fix bit operation.
TODO: Fix multible variable in one package.
TODO: # multiradade komentarer fungerar inte i loopar
"""

class ByteBuffer:
    def __init__(self):
        self._storage = bytearray()
        self._bitpos = 8
        self._curbitval = 0
        self._offset = 0  # Lägg till en offset-hantering

    def read_bit(self):
        """ Läs en bit åt gången från den aktuella byte-strängen """
        if self._bitpos == 8:
            self._curbitval = self._storage[self._offset]
            self._offset += 1
            self._bitpos = 0
        bit = (self._curbitval >> (7 - self._bitpos)) & 1
        self._bitpos += 1
        return bit

    def read_bits(self, bits):
        """ Läs flera bitar och returnera som ett heltal """
        value = 0
        for i in range(int(bits)):  # Se till att bits är ett heltal
            value = (value << 1) | self.read_bit()
        return value

    def read_bits_from_offset(self, bits, offset):
        """ Läs bitar med offset, använd read_bits för att läsa flera bitar åt gången """
        self._offset = offset  # Ställ in offsetet till den angivna platsen
        return self.read_bits(bits)  # Läs de angivna bitarna


class ModifierOperator:

    @staticmethod
    def modifier_parser(line, metadata, fields):
        """ Hanterar fältdefinitioner med metadata (modifierare som M, U) """
        field_name, field_type = line.split(":")
        field_type, metadata_info = field_type.split(",")
        s = ''.join(metadata_info.strip().split(','))
        
        if len(s) > 1:
            for char in s:
                char = char.strip()
                if field_name.strip() in metadata:
                    metadata[field_name.strip()].append(char)
                else:
                    metadata[field_name.strip()] = [char]
        else:
            metadata[field_name.strip()] = [metadata_info.strip()]
        
        fields.append((field_name.strip(), field_type.strip()))

        return metadata, fields

    @staticmethod
    def modifier_handler(field_name, field_value, field_type, metadata):
        """ Tillämpa modifierare baserat på metadata """
        if isinstance(field_value, bytes) and ("s" in field_type) and not ('ip' in field_name):
            try:
                field_value = field_value.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                field_value = field_value.hex()

        for modifier in metadata.get(field_name, []):
            if modifier in modifiers_opereration_mapping:
                field_value = modifiers_opereration_mapping[modifier](field_value)

        return field_value

    @staticmethod
    def to_hex(field_value):
        if isinstance(field_value, int):
            field_value = hex(field_value)
        elif isinstance(field_value, str):
            field_value = field_value.encode('utf-8').hex()

        return field_value
    
    @staticmethod
    def to_mirror(field_value):
        if isinstance(field_value, str): 
            return field_value[::-1]
        return field_value
    
    @staticmethod
    def to_lower(field_value):
        if isinstance(field_value, str): 
            return field_value.lower()
        return field_value
    
    @staticmethod
    def to_upper(field_value):
        if isinstance(field_value, str): 
            return field_value.upper()
        return field_value
    
    @staticmethod
    def to_ip_address(field_value):
        if isinstance(field_value, bytes):
            return ".".join(str(b) for b in field_value)
        return field_value
    
    @staticmethod
    def to_string(field_value):
        if isinstance(field_value, str): 
            return field_value.decode("utf-8").strip("\x00")
        return field_value
    
    @staticmethod
    def to_string_from_bytes(field_value):
        if isinstance(field_value, bytes):
            field_value = field_value.decode("utf-8").strip("\x00")
        return field_value            


modifiers_opereration_mapping = {
    "H": ModifierOperator.to_hex,
    "M": ModifierOperator.to_mirror,
    "s": ModifierOperator.to_string,
    "u": ModifierOperator.to_lower,
    "U": ModifierOperator.to_upper,
    "W": ModifierOperator.to_ip_address
}

class StructDefintion:
    @staticmethod
    def parse_struct_definition(struct_str, endianess = "<"):
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        metadata. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        fields = []
        dynamic_fields = {}
        metadata = {}
        block = {}

        lines = struct_str.strip().split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if '#' in line:
                line_test, n = WoWStructParser.handle_comments_and_blocks(lines, i)

                if not line_test[0]:
                    # print(lines)
                    #for line in lines[:]:  # Gör en kopia av listan för att undvika problem vid borttagning
                     #   if line.strip().startswith("#") or not line.strip():
                      #      lines.remove(line)
                    # print(lines)
                    i = i + 1
                    continue
                else:
                    lines[i] = line_test[0]
            
            if not line or line.startswith("header:") or line.startswith("data:"):
                i += 1
                continue  
            
            if line.startswith("endian:"):
                endianess = StructDefintion.check_endian(line)
                i += 1
                continue

            if 'block' in line:
                num, block_lines = WoWStructParser.handle_comments_and_blocks(lines, i)
                loop_match = re.match(r"block <(\w+)>:", lines[i].strip())

                variable_list = []

                if loop_match:
                    variable = loop_match.group(1)

                for b in block_lines:
                    try:
                        field_name, field_type = b.split(":")
                        variable_list.append((field_name.strip(), field_type.strip()))
                        
                    except ValueError as e:
                    # print(f"Value error: {e}")
                        print(lines[i])

                block[variable] = variable_list
                i += num + 1
                continue

            if 'loop' in line:
                num, _ = WoWStructParser.handle_comments_and_blocks(lines, i)
                
                loop_match = re.match(r"loop <(.*?)> as <(\w+)>:", lines[i].strip())

                if loop_match:
                    loop_count_variable = loop_match.group(1)
                    field_name = loop_match.group(2)

                loop_match = re.match(r"loop (\d+) as <(\w+)>:", lines[i].strip())

                if loop_match:
                    loop_count_variable = loop_match.group(1)
                    field_name = loop_match.group(2)
    
                fields.append(('loop', f"{loop_count_variable}", f"{field_name}", f"{num}"))

                i += 1
                continue

            if ":" in line and "," in line:
                metadata, fields = ModifierOperator.modifier_parser(line, metadata, fields)
                i += 1
                continue

            try:
                field_name, field_type = lines[i].split(":")
                fields.append((field_name.strip(), field_type.strip()))
            except ValueError as e:
               # print(f"Value error: {e}")
                print(lines[i])

            i += 1

           
        return endianess, fields, dynamic_fields, metadata, block

    @staticmethod
    def check_endian(line):
        endian_type = line.split(":")[1].strip()
        return "<" if endian_type == "little" else ">"
    

class WoWStructParser:
    """ 
    The WoWStructParser class is used to define and parse network packet structures (WoW-Struct format). 
    It reads the structure definition, handles dynamic fields, and applies the appropriate transformations 
    such as endianess, string mirroring, and IP formatting.
    """

    @staticmethod
    def handle_comments_and_blocks(lines, i):
        """
        Hanterar både kommentarer och block. Identifierar kommentarer som startar med # eller #- och slut på samma rad eller efter flera rader.
        Hanterar också block som loop, if, switch, bitmask och randseq.
        """
        
        line = lines[i]

        if line.startswith("#-"):
            while not lines[i].endswith("-#"):
                i += 1
            return None, i  
        elif "#" in line:
            if line.startswith("#"):
                return None, 1
            else:
                return [line.split("#")[0].strip()], 0
        elif line.strip().startswith("loop"):
            return WoWStructParser.handle_loop(lines, i)
        elif line.strip().startswith("block"):
            return WoWStructParser.handle_loop(lines, i)

    @staticmethod
    def handle_loop(lines, i):
        """Hantera loopar och räkna antalet indenterade rader"""
        block_lines = []
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])
        i = i + 1
        n = 0
        
        while i < len(lines) and len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
            if not lines[i].strip().startswith('#'):
                block_lines.append(lines[i].strip())
                n += 1
            i += 1

        return n, block_lines 

    @staticmethod
    def extract_data(raw_data, endianess, fields, metadata, block=None, offset=0, just=0):
        """
        Extracts data from the raw byte data based on the parsed fields and metadata. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """
        parsed_data = {}
        fmt = ""
        field_size = 0
        field_value = ""
        buffer = ByteBuffer()
        i = 0

       

        while i < len(fields):


            if len(fields[i]) == 2:
                field_name, field_type = fields[i]
            elif len(fields[i]) == 3:
                field_name, field_type, variable_name = fields[i]
            else:
                field_name, field_type, variable_name, loop_field = fields[i]
            
            pattern = r'<(.*?)>'
            match = re.search(pattern, field_type)

            if match and not 'include' in field_name:
                variable_name = match.group(1)
                field_type = str(parsed_data[variable_name]) + "s"
            
            if 'S' in field_type:
                data = raw_data[offset:].split(b'\x00')[0]
                length = len(data) + 1
                field_type = str(length) + "s"

            try:
                ignore_field = ['loop', 'include']
                ignore_modifier = ['bits', 'bit']

                if (field_name not in ignore_field) and not (any(field_type.startswith(prefix) for prefix in ignore_modifier)):
                    fmt = f"{endianess}{field_type}" 
                    field_size = struct.calcsize(fmt)
            except struct.error:
                    print(f"Error calculating size for format: {fmt}")
                    continue
            try:
                if 'bit' in field_type:
                    match = re.match(r"bit(\d*)", field_type)

                    if match:
                        buffer._storage = bytearray(raw_data) 
                        bit_length = match.group(1) if match.group(1) else 1  
                        print(f"Variable: {field_name}, Bit length: {bit_length}")

                        
                        field_value = buffer.read_bits_from_offset(bit_length, offset) +1
                        offset += 1  


                    i += 1
                    continue
                elif 'include' in field_name:
                    pattern = r'<(.*?)>'
                    match = re.search(pattern, field_type)

                    parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, block[match.group(1)], metadata, block, offset, just=4)
                    i += len(parsed_loop) + 1
                    parsed_data.update(parsed_loop)
                    continue
                elif 'loop' in field_name:
                    try:
                        loop = int(field_type)
                    except ValueError:
                        loop = int(parsed_data[field_type])                 

                    n = i + 1
                    loop_fields = fields[n:n + int(loop_field)]
                    variable_list = []
                    for x in range(loop):
                        print(f'Loop {x}')
                        parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, loop_fields, metadata, block, offset, just=4)
                        variable_list.append(parsed_loop)
                    
                    i += len(loop_fields) + 1
                    parsed_data[variable_name] = variable_list
                    continue
                elif 's' in field_type:
                    field_value = struct.unpack_from(fmt, raw_data, offset)[0]
                elif re.match(r'^\d+[A-Za-z]$', field_type):
                    field_value = struct.unpack_from(fmt, raw_data, offset)
                elif (len(fmt) > 2 and 'C' in metadata.get(field_name, []) and (field_type not in ignore_modifier)): 
                    field_value = struct.unpack_from(fmt, raw_data, offset)

                    combined = 0

                    for value in field_value:
                        combined += value

                    field_value = combined
                else:
                    if fmt:
                        field_value = struct.unpack_from(fmt, raw_data, offset)[0]
            except struct.error as e:
                print(f'Error parsing data: {e}')
                print(parsed_data)
                print("Continue with next package\n\n")
                break

            if field_name.startswith('_') or field_name.startswith('ignored'):
                offset += field_size
                i += 1
                continue
                
            if field_name in metadata:
                field_value = ModifierOperator.modifier_handler(field_name, field_value, field_type, metadata)
                parsed_data[field_name] = field_value
            else:
                if "s" in field_type:
                    field_value = ModifierOperator.to_string_from_bytes(field_value)
                    parsed_data[field_name] = field_value
                   
                else:
                    parsed_data[field_name] = field_value
                    
                            
            if just:
                print(f"{'':>4}Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
            else:
                print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
            
            offset += field_size
            i += 1

        return parsed_data, offset

    @staticmethod
    def load_file(file_path):
        """ Loads file content as a string """
        with open(file_path, "r") as file:
            return file.read()

    @staticmethod
    def load_bin_file(file_path):
        """ Loads binary file content """
        with open(file_path, "rb") as file:
            return file.read()

    @staticmethod
    def load_json_file(file_path):
        """ Loads json file (for simplicity, assuming it's a JSON for now) """
        with open(file_path, "r") as file:
            return json.load(file)
        
    @staticmethod
    def parse_case(version, case):
         # Om ett specifikt case anges, kör det.
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"
        json_file = f"build/{version}/json/{case}.json"

        # Ladda och bearbeta filerna
        struct_definition = WoWStructParser.load_file(def_file)
        raw_data = WoWStructParser.load_bin_file(bin_file)
        expected_output = WoWStructParser.load_json_file(json_file)

        print(case)
        print(f"{struct_definition}\n")
        # Parsning och extrahering
        endianess, fields, dynamic_fields, metadata, block = StructDefintion.parse_struct_definition(struct_definition)
        # print(metadata)

        parsed_data, _ = WoWStructParser.extract_data(raw_data, endianess, fields, metadata, block)

        # Utskrift
        print()
        print(f"Raw Data: \n{raw_data}")
        print(f"Len raw data: {len(raw_data)}")
        print("\nParsed Data: \n", json.dumps(parsed_data, indent=4))
        print("\nExpected Output: \n", json.dumps(expected_output, indent=4))

        if parsed_data == expected_output:
            print("Match\n\n")
        
    @staticmethod
    def parse_case_unittest(version, case):
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"
        json_file = f"build/{version}/json/{case}.json"

        struct_definition = WoWStructParser.load_file(def_file)
        raw_data = WoWStructParser.load_bin_file(bin_file)
        expected_output = WoWStructParser.load_json_file(json_file)

        endianess, fields, dynamic_fields, metadata = StructDefintion.parse_struct_definition(struct_definition,)
        parsed_data, _ = WoWStructParser.extract_data(raw_data, endianess, fields, metadata, debug=False)

        return parsed_data


if __name__ == "__main__":

    version = sys.argv[1] if len(sys.argv) > 1 else "18414"
    case = sys.argv[2] if len(sys.argv) > 2 else None

    if case:
        WoWStructParser.parse_case(version, case)
    else:
        for case_file in os.listdir(f"build/{version}/def"):
            if case_file.endswith(".def"):
                case = case_file.replace(".def", "")
                WoWStructParser.parse_case(version, case)