#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import re
import sys

from modules.blockHandler import BlockInterPreter
from modules.bitsHandler import BitInterPreter
from modules.loopHandler import LoopInterPreter
from modules.modifierHandler import ModifierInterPreter
from modules.randseqHandler import RandseqInterPreter
from modules.structHandler import StructInterPreter
from utils.fileUtils import FileHandler
from utils.parseUtils import ParsingUtils, get_values

"""
TODO: Fix bit operation.
TODO: Fix randseq
"""

class StructDefintion:
    @staticmethod
    # def parse_struct_definition(lines, parameters, endianess = "<", debug=True):
    def parse_struct_definition(parameters: dict) -> dict:
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        modifiers. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        endianess, fields, modifiers, lines = get_values(parameters, "endianess", "fields", "modifiers", "struct_definition_list")
               
        i = 0

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
                modifiers, fields = ModifierInterPreter.parser(line, modifiers, fields)
                parameters['modifiers'].update(modifiers)
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
    # def extract_data(raw_data, endianess, fields, modifiers, block=None, offset=0, just=0, debug=True):
        """
        Extracts data from the raw byte data based on the parsed fields and modifiers. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """

        # endianess, fields, modifiers, block, raw_data, debug, struct_definition_list, just, offset = parameters.values()

        endianess, fields, modifiers, raw_data, debug, just, offset, i, parsed_data = get_values(parameters,
            "endianess", "fields", "modifiers", "raw_data", "debug", "just", "offset", "i", "parsed_data"
        )

        while i < len(fields):
            field = fields[i]
            field_name = field[0]
            field_type = field[1]
           
            # Check special string cases. ex. variables and terminator
            field_type = ParsingUtils.resolve_string_field_type(field_type, raw_data, offset, parsed_data)

            if 'bit' in field_type:
                pass
            elif 'include' in field_name:
                parameters = BlockInterPreter.include_handler(parameters)
                i, offset, parsed_data = get_values(parameters, "i", "offset", "parsed_data")
                continue
            elif 'loop' in field_name:
                parameters = LoopInterPreter.extractor(parameters)
                i, offset, parsed_data = get_values(parameters, "i", "offset", "parsed_data")
                continue                    
            elif 'randseq' in field_name:
                loop = int(field_type)

                n = i + 1
                randseq_fields = fields[n:n + loop]

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

            try:
               # Parse using struct
                fmt = f"{endianess}{field_type}"
                field_size = struct.calcsize(fmt)

                # Ignore field (e.g. padding), just advance
                if field_name.startswith('_'):
                    print("yes")
                    i += 1
                    offset += field_size

                    parameters["offset"] = offset
                    parameters["i"] = i
                    continue

                # Unpack raw value
               
                if 's' in field_type:
                    field_value = struct.unpack_from(fmt, raw_data, offset)[0]
                    field_value = ModifierInterPreter.to_string_from_bytes(field_value)
                elif re.match(r'^\d+[A-Za-z]$', field_type):
                    field_value = struct.unpack_from(fmt, raw_data, offset)
                elif len(fmt) > 2 and 'C' in modifiers.get(field_name, []):
                    field_value = struct.unpack_from(fmt, raw_data, offset)
                else:
                   field_value = struct.unpack_from(fmt, raw_data, offset)[0]


                if field_name in modifiers:
                    field_value = ModifierInterPreter.modifier_handler(field_name, field_value, field_type, modifiers)
                else:
                    # field_value = field_value if isinstance(field_value, tuple) else field_value
                    pass

                # Store parsed result
                parsed_data[field_name] = field_value

                # Optional debug print
                debug and print(
                    f"{'':>{just}}Field: {field_name}, Offset: {offset}, Size: {field_size}, "
                    f"fmt: {fmt}, Data: {raw_data[offset:offset + field_size]}, Parsed: {field_value}"
                )

                # Advance
                offset += field_size
                i += 1

                # Update parser state
                parameters.update({
                    "parsed_data": parsed_data,
                    "offset": offset,
                    "i": i
                })
            except (struct.error, IndexError, KeyError, ValueError) as e:
                # Advance
                # offset += field_size
                # i += 1

                if debug:
                    print(f"{'':>{just}}[ERROR] Failed to parse field '{field_name}' with fmt '{fmt}': {e}")
                continue

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
        parameters = ParsingUtils.init_parameters(raw_data, struct_definition_list)
        parameters = StructDefintion.parse_struct_definition(parameters)

        print(f'Endian: {parameters['endianess']}\n')
        print(f'Fields: {parameters['fields']}\n')
        print(f'Modifiers: {parameters['modifiers']}\n')
        print(f'Block: {parameters['block']}\n')

        parsed_data, _ = WoWStructParser.extract_data(parameters)
        
        try:
            print()
            print(f"Raw Data: \n{raw_data}")
            print(f"Len raw data: {len(raw_data)}")
            print("\nParsed Data: \n", json.dumps(parsed_data, indent=4))
            print("\nExpected Output: \n", json.dumps(expected_output, indent=4))
        except TypeError:
            print()
            print(f"Raw Data: \n{raw_data}")
            print(f"Len raw data: {len(raw_data)}")
            print("\nParsed Data: \n", parsed_data)
            print("\nExpected Output: \n", expected_output)

        if parsed_data == expected_output:
            print("Match\n\n")
        
    @staticmethod
    def parse_case_unittest(version, case):
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"

        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)
        parameters = ParsingUtils.init_parameters(raw_data, struct_definition_list)

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