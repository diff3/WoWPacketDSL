#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import re
import sys
import time

from modules.blockHandler import BlockInterPreter
from modules.bitsHandler import BitInterPreter
from modules.loopHandler import LoopInterPreter
from modules.modifierHandler import ModifierInterPreter
from modules.randseqHandler import RandseqInterPreter
from modules.structHandler import StructInterPreter
from utils.fileUtils import FileHandler
from utils.parseUtils import ParsingUtils


"""
TODO: Fix bit operation.
TODO: Det går att ha flera variabler, men ibland är in parse filen nåbar, som i looper, då kan man bara använda variabler inom loopen
TODO: har man kommentarer på flera rader så påverkar det raden innan kommentaren.
"""


class StructDefintion:
    @staticmethod
    # def parse_struct_definition(lines, parameters, endianess = "<", debug=True):
    def parse_struct_definition(parameters: dict) -> dict:
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        metadata. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        endianess, fields, metadata, block, raw_data, debug, struct_definition_list, just, offset = parameters.values()
        
        i = 0
  
        lines = struct_definition_list

        while i < len(lines):
            line = lines[i].strip()
          
            if line.startswith("endian:"):
                endianess = StructDefintion.check_endian(line)
                parameters['endianess'] = endianess
                i += 1
                continue
            
            if line.startswith('block'):
                variable, variable_list, num = BlockInterPreter.parser(lines, i)
                parameters['block'].update({variable: variable_list})
                i += num
                continue
            
            if line.startswith('loop'):
                parameters['fields'].append(LoopInterPreter.parser(lines, i))
                i += 1
                continue
            
            if line.startswith('randseq'):
                parameters['fields'].append(RandseqInterPreter.parser(lines, i))
                i += 1
                continue
                
            # This is struct with modifier
            if ":" in line and "," in line:
                metadata, fields = ModifierInterPreter.parser(line, metadata, fields)
                parameters['metadata'].update(metadata)
                i += 1
                continue

            # Just struct
            if ":" in line:
                parameters['fields'].append(StructInterPreter.parser(lines, i))
                i += 1
                continue
            
            i += 1

        return parameters

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
    def extract_data(parameters):
    # def extract_data(raw_data, endianess, fields, metadata, block=None, offset=0, just=0, debug=True):
        """
        Extracts data from the raw byte data based on the parsed fields and metadata. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """

        endianess, fields, metadata, block, raw_data, debug, struct_definition_list, just, offset = parameters.values()

        parsed_data = {}
        fmt = ""
        field_size = 0
        field_value = ""
        

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

                    parsed_loop, offset = WoWStructParser.extract_data(parameters)
                    # parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, block[match.group(1)], metadata, block, offset, just=4, debug=False)
                    i += len(parsed_loop) + 1
                    parsed_data.update(parsed_loop)
                    # print(parsed_data)
                    continue
                elif 'loop' in field_name:
                    loop = int(parsed_data[field_type])                 
                    loop_fields = fields[i + 1:i + 1 + int(loop_field)]
                    variable_list = []

                    for x in range(loop):
                        if debug:
                            print(f'Loop {x}')
                        
                        loop_parameters = parameters
                        loop_parameters.update({'fields': loop_fields, 'offset': offset, 'just': 4})

                        parsed_loop, offset = WoWStructParser.extract_data(loop_parameters)
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
                    
                    addon_size = int.from_bytes(raw_data[54:58], byteorder='little')
                    # print(parsed_data_randseq)
                    addon_data_start = 58


                    addon_data_end = addon_data_start + addon_size
                    parsed_data_randseq["addon_size"] = addon_size
                    parsed_data_randseq["addon_data"] = raw_data[addon_data_start:addon_data_end].hex()

                    test = raw_data[addon_data_end:]

                    # Läs en bit
                    byte_pos = 0
                    bit_pos = 0

                    # Läs första biten
                    bit, byte_pos, bit_pos = BitInterPreter.read_bit(test, byte_pos, bit_pos)
                    # print(f"Bit: {bit}, New byte_pos: {byte_pos}, New bit_pos: {bit_pos}")

                    # parsed_data_randseq["_"] = test[byte_pos + 1:byte_pos + 1 + int(bits)]


                    # Läs nästa 11 bitar
                    bits, byte_pos, bit_pos = BitInterPreter.read_bits(test, byte_pos, bit_pos, 11)
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
                field_value = ModifierInterPreter.modifier_handler(field_name, field_value, field_type, metadata)
                parsed_data[field_name] = field_value
            else:
                if "s" in field_type:
                    field_value = ModifierInterPreter.to_string_from_bytes(field_value)
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
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"
        json_file = f"build/{version}/json/{case}.json"

        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)
        expected_output = FileHandler.load_json_file(json_file)

        print(case)
        print(f"{struct_definition}\n")

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)

        parameters = {
            "endianess": "<",
            "fields": [],
            "metadata": {},
            "block": {},
            "raw_data": raw_data,  
            "debug": True,
            "struct_definition_list": struct_definition_list,
            "just": 0, 
            "offset": 0
        }

        parameters = StructDefintion.parse_struct_definition(parameters)

        print(f'Endian: {parameters['endianess']}\n')
        print(f'Fields: {parameters['fields']}\n')
        print(f'Metadata: {parameters['metadata']}\n')
        print(f'Block: {parameters['block']}\n')

        parsed_data, _ = WoWStructParser.extract_data(parameters)
        
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

        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)

        parameters = {
            "endianess": "<",
            "fields": [],
            "metadata": {},
            "block": {},
            "raw_data": raw_data,  
            "debug": False,
            "struct_definition_list": struct_definition_list,
            "just": 0, 
            "offset": 0
        }

        parameters = StructDefintion.parse_struct_definition(parameters)
        parsed_data, _ = WoWStructParser.extract_data(parameters)
        
        return json.dumps(parsed_data)


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