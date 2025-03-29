#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import re
import sys
import time

from modules.bitsHandler import BitReader
from modules.loopHandler import LoopInterPreter
from modules.modifierHandler import ModifierOperator
from utils.fileUtils import FileHandler
from utils.parseUtils import ParsingUtils


"""
TODO: Fix bit operation.
TODO: Det går att ha flera variabler, men ibland är in parse filen nåbar, som i looper, då kan man bara använda variabler inom loopen
TODO: har man kommentarer på flera rader så påverkar det raden innan kommentaren.
"""


class StructDefintion:
    @staticmethod
    def parse_struct_definition(lines, endianess = "<", debug=True):
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        metadata. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        fields = []
        dynamic_fields = {}
        metadata = {}
        block = {}

        i = 0

        while i < len(lines):
            line = lines[i].strip()
          
            if line.startswith("endian:"):
                endianess = StructDefintion.check_endian(line)
                i += 1
                continue

            if 'block' in line:
                result = WoWStructParser.handle_comments_and_blocks(lines, i)
                num = result[0]
                block_lines = result[1]

                loop_match = re.match(r"block <(\w+)>:", lines[i].strip())

                variable_list = []

                if loop_match:
                    variable = loop_match.group(1)

                for b in block_lines:
                    try:
                        field_name, field_type = b.split(":")
                        variable_list.append((field_name.strip(), field_type.strip()))
                        
                    except ValueError as e:
                        if debug:
                            print(f"Value error: {e}")
                            print(lines[i])


                block[variable] = variable_list
                i += num + 1
                continue
            if 'loop' in line:
                fields.append(LoopInterPreter.parser(lines, i))
                i += 1
                continue
            if 'randseq' in line:
                result = WoWStructParser.handle_comments_and_blocks(lines, i)
                num = result[0]
                block_lines = result[1]
                loop_match = re.match(r"randseq (\d+) as <(\w+)>:", lines[i].strip())

                if loop_match:
                    length_in_bytes = loop_match.group(1)
                    variable_name = loop_match.group(2)
                else:
                    print("helojfewöfijwelfjhewj")

               
                fields.append(('randseq', f"{length_in_bytes}", f"{variable_name}", f"{num}"))
                print(f'randseq {length_in_bytes}, {variable_name}, {num}')
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
                if debug:
                    print(f"Value error: {e}")
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

        if line.strip().startswith("randseq"):
            return ParsingUtils.count_size_of_block_structure(lines, i)
        elif line.strip().startswith("block"):
            return ParsingUtils.count_size_of_block_structure(lines, i)
        elif line.strip().startswith("if"):
            return ParsingUtils.count_size_of_block_structure(lines, i)
        
        return False
    

    @staticmethod
    def extract_data(raw_data, endianess, fields, metadata, block=None, offset=0, just=0, debug=True):
        """
        Extracts data from the raw byte data based on the parsed fields and metadata. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """
        parsed_data = {}
        fmt = ""
        field_size = 0
        field_value = ""
        # buffer = BitReader.ByteBuffer()
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
                ignore_field = ['loop', 'include', 'block', 'randseq']
                ignore_modifier = ['bits', 'bit']

                if (field_name not in ignore_field) and not (any(field_type.startswith(prefix) for prefix in ignore_modifier)):
                    fmt = f"{endianess}{field_type}" 
                    field_size = struct.calcsize(fmt)
            except struct.error:
                    if debug:
                        print(f"Error calculating size for format: {fmt}")
                    continue
            try:
                if 'bit' in field_type:
                    match = re.match(r"bit(\d*)", field_type)

                    if match:
                        buffer._storage = bytearray(raw_data) 
                        bit_length = match.group(1) if match.group(1) else 1  
                        if debug:
                            print(f"Variable: {field_name}, Bit length: {bit_length}")

                        
                        field_value = buffer.read_bits_from_offset(bit_length, offset) +1
                        offset += 1  


                    i += 1
                    continue
              
                elif 'include' in field_name:
                    pattern = r'<(.*?)>'
                    match = re.search(pattern, field_type)

                    parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, block[match.group(1)], metadata, block, offset, just=4, debug=False)
                    i += len(parsed_loop) + 1
                    parsed_data.update(parsed_loop)
                    # print(parsed_data)
                    continue
                elif 'loop' in field_name:
                    try:
                        loop = int(field_type)
                    except ValueError:
                        loop = int(parsed_data[field_type])                 

                    n = i + 1
                    loop_fields = fields[n:n + int(loop_field)]
                    print(type(loop_field))
                    variable_list = []
                    for x in range(loop):
                        if debug:
                            print(f'Loop {x}')
                        parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, loop_fields, metadata, block, offset, just=4, debug=False)
                        variable_list.append(parsed_loop)

                        if offset > len(raw_data):
                            break
                    
                    i += len(loop_fields) + 1
                    parsed_data[variable_name] = variable_list
                  
                    continue
                elif 'randseq' in field_name:
                    loop = int(field_type)

                    n = i + 1
                    randseq_fields = fields[n:n + int(loop_field)]

                    randseq_definition = {}

                    for field in randseq_fields:
                        print([field[0]])
                        print([field[1]])
                        if not '-' in field[1] and ' ' in field[1]:
                            randseq_definition[field[0]] = [int(x) for x in field[1].split(' ')]
                        elif  '-' in field[1]:
                            randseq_definition[field[0]] = tuple(field[1].split('-'))
                        elif not '-' in field[1]:
                            randseq_definition[field[0]] = field[1]
                        elif '><' in field[1]:
                            print("patters")
                            pattern = r'<(\w+)><(\w+)>'
                            match = re.search(pattern, field[1])
                            print(match)


                    print(randseq_definition)

                    parsed_data_randseq = {}

                    for key, value in randseq_definition.items():
                        if isinstance(value, list):  # Om det är en lista av bytes
                            parsed_data_randseq[key] = [f"{raw_data[index]:02X}" for index in value]
                            parsed_data_randseq[key] = "".join(parsed_data_randseq[key])
                        
                        elif isinstance(value, tuple):  # Om det är en tuple av start och slut position
                            start, end = value
                            parsed_data_randseq[key] = int.from_bytes(raw_data[int(start):int(end)], byteorder='little')
                    '''
                    addon_size = int.from_bytes(raw_data[54:58], byteorder='little')'''
                    print(parsed_data_randseq)
                    addon_data_start = 58


                    addon_data_end = addon_data_start + addon_size
                    parsed_data_randseq["addon_size"] = addon_size
                    parsed_data_randseq["addon_data"] = raw_data[addon_data_start:addon_data_end].hex()

                    test = raw_data[addon_data_end:]

                    # Läs en bit
                    byte_pos = 0
                    bit_pos = 0

                    # Läs första biten
                    bit, byte_pos, bit_pos = BitReader.read_bit(test, byte_pos, bit_pos)
                    # print(f"Bit: {bit}, New byte_pos: {byte_pos}, New bit_pos: {bit_pos}")

                    # parsed_data_randseq["_"] = test[byte_pos + 1:byte_pos + 1 + int(bits)]


                    # Läs nästa 11 bitar
                    bits, byte_pos, bit_pos = BitReader.read_bits(test, byte_pos, bit_pos, 11)
                    # print(f"Bits: {bits}, New byte_pos: {byte_pos}, New bit_pos: {bit_pos}")
                    parsed_data_randseq["user_length"] = int(bits)

                    # Hoppa över de första två bytena och skriv ut återstående data
                    # print(test[byte_pos + 1:byte_pos + 1 + int(bits)])  # Hoppa över 2 byte och skriv ut de 4 återstående
                    parsed_data_randseq["user"] = test[byte_pos + 1:byte_pos + 1 + int(bits)].decode()
                    parsed_data.update(parsed_data_randseq)           

                    i += int(loop_field) + 1
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
                if debug:
                    print(f'Error parsing data: {e}')
                    print(parsed_data)
                    print("Continue with next package\n\n")
                break

            if field_name.startswith('_') or field_name.startswith('ignore'):
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
                    
                            
            if debug:
                if just:
                    print(f"{'':>4}Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
                else:
                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
            
            offset += field_size
            i += 1

        return parsed_data, offset

        
    @staticmethod
    def parse_case(version, case):
         # Om ett specifikt case anges, kör det.
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"
        json_file = f"build/{version}/json/{case}.json"

        # Ladda och bearbeta filerna
        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)
        expected_output = FileHandler.load_json_file(json_file)

        print(case)
        print(f"{struct_definition}\n")

        # Clean it
        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)

        # Parsning och extrahering
        endianess, fields, dynamic_fields, metadata, block = StructDefintion.parse_struct_definition(struct_definition_list)
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

        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)
        expected_output = FileHandler.load_json_file(json_file)

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)

        endianess, fields, dynamic_fields, metadata, block = StructDefintion.parse_struct_definition(struct_definition_list, debug=False)

        parsed_data, _ = WoWStructParser.extract_data(raw_data, endianess, fields, metadata, block, debug=False)

        test = json.dumps(parsed_data)



        return test


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