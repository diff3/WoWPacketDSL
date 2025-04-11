#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import sys

from modules.blockHandler import BlockInterPreter
# from modules.ifHandler import IfInterPrePreter
from modules.loopHandler import LoopInterPreter
from modules.modifierHandler import ModifierInterPreter
from modules.randseqHandler import RandseqInterPreter
from modules.structHandler import StructInterPreter
from utils.fileUtils import FileHandler
from utils.parseUtils import ParsingUtils, extract_struct_field, apply_modifiers
from modules.context import get_context

from utils.ConfigLoader import ConfigLoader
from utils.Logger import Logger

# GLOBALS
config = ConfigLoader.load_config()

"""
TODO: Fix komma åt alla variabler, även i och utanför ex. looper
TODO: Fix randseq
"""


class StructDefintion:
    @staticmethod
    def parse_struct_definition():
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        modifiers. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        ctx = get_context()
        endianess, fields, modifiers, lines, debug = ctx.get_values("endianess", "fields", "modifiers", "struct_definition_list", "debug")

        i = 0

        while i < len(lines):
            line = lines[i].strip()
            debug and print(f"[DEBUG] Line {i}: {lines[i]}")
          
            if line.startswith("endian:"):
                endianess = ParsingUtils.check_endian(line)
                ctx.endianess = endianess
                i += 1
                continue

            if line.startswith('block'):
                variable, variable_list, num = BlockInterPreter.parser(lines, i)
                ctx.block.update({variable: variable_list})
                i += num
                continue
            
            if line.startswith('loop'):
                field = LoopInterPreter.parser(lines, i)
                get_context().fields.append(field)
                i += 1
                continue
            
            if line.startswith('randseq'):
                ctx.fields.append(RandseqInterPreter.parser(lines, i))
                i += 1
                continue
                            
            # This is struct with modifier
            if ":" in line and "," in line:
                modifiers, fields = ModifierInterPreter.parser(line, modifiers, fields)
                ctx.modifiers.update(modifiers)
                i += 1
                continue

            # Just struct
            if ":" in line:
                field = StructInterPreter.parser(lines, i)
                get_context().fields.append(field)
                i += 1
                continue
            
            i += 1


class WoWStructParser:
    """ 
    The WoWStructParser class is used to define and parse network packet structures (WoW-Struct format). 
    It reads the structure definition, handles dynamic fields, and applies the appropriate transformations 
    such as endianess, string mirroring, and IP formatting.
    """

    @staticmethod
    def extract_data(ctx=None):
        """
        Extracts data from the raw byte data based on the parsed fields and modifiers. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """

        if ctx is None:
            ctx = get_context()

        endianess, fields, modifiers, raw_data, debug, just, offset, i, parsed_data = ctx.get_values(
            "endianess", "fields", "modifiers", "raw_data", "debug", "just", "offset", "i", "parsed_data"
        )

        while i < len(fields):
            field = fields[i]
            field_name = field[0]
            field_type = field[1]
           
            # Check special string cases. ex. variables and terminator
            field_type = ParsingUtils.resolve_string_field_type(field_type, raw_data, offset)

            if 'include' in field_name:
                BlockInterPreter.include_handler()
                i, offset, parsed_data = ctx.get_values("i", "offset", "parsed_data")
                continue
            elif 'loop' in field_name:
                LoopInterPreter.extractor()
                i, offset, parsed_data = ctx.get_values("i", "offset", "parsed_data")
                continue                    
            elif 'randseq' in field_name:
                RandseqInterPreter.extractor()
                i, offset, parsed_data = ctx.get_values("i", "offset", "parsed_data")
                continue                    

            try:
                # Unpack raw value using stuct

                # Ignore fields prefixed with '_'
                if field_name.startswith('_'):
                    i += 1
                    offset += field_size
                    ctx.set_values(i=i, offset=offset)
                    continue
                
                field_value, field_size, fmt = extract_struct_field(field_name, field_type, raw_data, offset, modifiers, endianess, parsed_data)
                
                # Apply modifiers
                field_value = apply_modifiers(field_name, field_value, modifiers, field_type)
        
                parsed_data[field_name] = field_value
                
                # Optional debug print
                # debug and print(
                  #  f"{'':>{just}}Field: {field_name}, Offset: {offset}, Size: {field_size}, "
                   # f"fmt: {fmt}, Data: {raw_data[offset:offset + field_size]}, Parsed: {field_value}"
               # )

                Logger.debug( 
                    f"{'':>{just}}Field: {field_name}, Offset: {offset}, Size: {field_size}, "
                    f"fmt: {fmt}, Data: {raw_data[offset:offset + field_size]}, Parsed: {field_value}")

                if i + 1 < len(fields):
                    next_field_name = fields[i + 1][0]
                    next_mods = modifiers.get(next_field_name, [])
                else:
                    next_mods = []
                
                if not any(m.endswith("B") for m in next_mods):
                    if not any(m.endswith("B") for m in modifiers):
                        offset = ctx.offset + ctx.byte_pos + field_size
                        ctx.set_values(bit_pos=0, byte_pos=0)
                    else:
                        offset += field_size

                    ctx.offset = offset
                else:
                    pass

                i += 1

                ctx.set_values(parsed_data=parsed_data, i=i)
            except (struct.error, IndexError, KeyError, ValueError) as e:
                offset += field_size
                i += 1
                Logger.error(f"{'':>{just}}[ERROR] Failed to parse field '{field_name}' with fmt '{fmt}': {e}")
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
        Logger.info(case)
        # print(case)

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)
        # print(f"{ json.dumps(struct_definition_list,indent=4)}\n")

        ctx = get_context()

        ctx.raw_data = raw_data
        ctx.struct_definition_list = struct_definition_list
        ctx.debug = True
       
        StructDefintion.parse_struct_definition()

        # print(f'Endian: {json.dumps(ctx.endianess)}\n')
        # print(f'Fields: {format_json_inline_list(ctx.fields)}')
        # print(f'Modifiers: {format_json_inline_list(ctx.modifiers)}')
        # print(f'Block: {format_json_inline_list(ctx.block)}')
        
        parsed_data = WoWStructParser.extract_data()[0]
        
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
            Logger.success("Match\n\n")
        
    @staticmethod
    def parse_case_unittest(version, case):
        def_file = f"build/{version}/def/{case}.def"
        bin_file = f"build/{version}/bin/{case}.bin"

        struct_definition = FileHandler.load_file(def_file)
        raw_data = FileHandler.load_bin_file(bin_file)

        struct_definition_list = ParsingUtils.remove_comments_and_reserved(struct_definition)

        ctx = get_context()
        ctx.raw_data = raw_data
        ctx.struct_definition_list = struct_definition_list
        ctx.debug = False
       
        StructDefintion.parse_struct_definition()

        parsed_data = WoWStructParser.extract_data()[0]
        
        return json.dumps(parsed_data)


if __name__ == "__main__":

    Logger.reset_log()
    
    version = sys.argv[1] if len(sys.argv) > 1 else "18414"
    case = sys.argv[2] if len(sys.argv) > 2 else None

    if case:
        WoWStructParser.parse_case(version, case)
    else:
        for case_file in os.listdir(f"build/{version}/def"):
            if case_file.endswith(".def"):
                case = case_file.replace(".def", "")
                WoWStructParser.parse_case(version, case)