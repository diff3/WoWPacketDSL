#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct
import os
import re
import sys


class WoWStructParser:
    """ 
    The WoWStructParser class is used to define and parse network packet structures (WoW-Struct format). 
    It reads the structure definition, handles dynamic fields, and applies the appropriate transformations 
    such as endianess, string mirroring, and IP formatting.
    """

    @staticmethod
    def handle_field_with_metadata(line, metadata, fields):
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
    def apply_field_modifiers(field_name, field_value, field_type, metadata):
        """ Hanterar modifierare (W, M, U, u) för ett fältvärde baserat på metadata """
        
        for meta in metadata[field_name]:
            if meta == "W" and isinstance(field_value, bytes):
                field_value = ".".join(str(b) for b in field_value)

            if isinstance(field_value, bytes) and "s" in field_type:
                try:
                    field_value = field_value.decode("utf-8").strip("\x00")
                except UnicodeDecodeError:
                    field_value = field_value.hex()
            if meta == "M" and isinstance(field_value, str):
                field_value = field_value[::-1]
            elif meta == "U" and isinstance(field_value, str):
                field_value = field_value.upper()
            elif meta == "u" and isinstance(field_value, str):
                field_value = field_value.lower()
            elif meta == "H":
                if isinstance(field_value, int):
                    field_value = hex(field_value)
                elif isinstance(field_value, str):
                    field_value = field_value.encode('utf-8').hex()

        return field_value
 
    @staticmethod
    def parse_struct_definition(struct_str, endianess = "<"):
        """
        Parses the structure definition from a given string and returns a list of fields, dynamic fields, and 
        metadata. It handles endian, dynamic fields, and other modifiers like M (mirrored) and W (ip).
        """

        fields = []
        dynamic_fields = {}
        metadata = {}

        lines = struct_str.strip().split("\n")
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if not line or line.startswith("#") or line.startswith("header:") or line.startswith("data:"):
                i += 1
                continue  

            if line.startswith("endian:"):
                endian_type = line.split(":")[1].strip()
                endianess = "<" if endian_type == "little" else ">"
                i += 1
                continue

            if ":" in line and "," in line:
                WoWStructParser.handle_field_with_metadata(line, metadata, fields)
                i += 1
                continue

            field_name, field_type = lines[i].split(":")
            fields.append((field_name.strip(), field_type.strip()))

            i += 1

        return endianess, fields, dynamic_fields, metadata

    @staticmethod
    def extract_data(raw_data, endianess, fields, dynamic_fields, metadata):
        """
        Extracts data from the raw byte data based on the parsed fields and metadata. It applies transformations 
        or dynamic fields, mirrored strings, and IP addresses as defined in the structure.
        """

        parsed_data = {}
        offset = 0

        for field_name, field_type in fields:
            pattern = r'<(.*?)>'
            match = re.search(pattern, field_type)

            if match:
                variable_name = match.group(1)
                field_type = str(parsed_data[variable_name]) + "s"
            
            #try:
            if not 'S' in field_type:
                fmt = f"{endianess}{field_type}" 
                field_size = struct.calcsize(fmt)
            #except struct.error:
             #   print(f"Error calculating size for format: {fmt}")
              #  return None
            
            try:
                if 's' in field_type:
                    field_value = struct.unpack_from(fmt, raw_data, offset)[0]
                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
                elif 'S' in field_type:
                    print("unknown")
                    data = raw_data[offset:].split(b'\x00')[0]
                    length = len(data) + 1 # x00 i removed in split

                    field_value = struct.unpack_from(f'{length}s', raw_data, offset)[0]
                    field_size = length
                    field_type = "s"
                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
                elif re.match(r'^\d+[A-Za-z]$', field_type):
                    field_value = struct.unpack_from(fmt, raw_data, offset)
                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
                elif len(fmt) > 2: 
                    field_value = struct.unpack_from(fmt, raw_data, offset)

                    combined = 0

                    for value in field_value:
                        combined += value

                    field_value = combined

                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
                else:
                    field_value = struct.unpack_from(fmt, raw_data, offset)[0]
                    print(f"Field: {field_name}, Offset: {offset}, Size: {field_size}, fmt: {fmt}, Data: {raw_data[offset:offset+field_size]}, Parsed: {field_value}")
            except struct.error as e:
                print(f'Error parsing data: {e}')
                print(parsed_data)
                print("Continue with next package\n\n")
                break
            
            offset += field_size

            if field_name in metadata:
                field_value = WoWStructParser.apply_field_modifiers(field_name, field_value, field_type, metadata)
                parsed_data[field_name] = field_value

            if not field_name in metadata:
      
                if isinstance(field_value, bytes) and "s" in field_type:
                    try:
                        field_value = field_value.decode("utf-8").strip("\x00")
                    except UnicodeDecodeError:
                        field_value = field_value.hex()
                
                parsed_data[field_name] = field_value

        print()
        return parsed_data

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
        endianess, fields, dynamic_fields, metadata = WoWStructParser.parse_struct_definition(struct_definition)
        parsed_data = WoWStructParser.extract_data(raw_data, endianess, fields, dynamic_fields, metadata)

        # Utskrift
        print(f"Raw Data: \n{raw_data}")
        print(f"Len raw data: {len(raw_data)}")
        print("\nParsed Data: \n", json.dumps(parsed_data, indent=4))
        print("\nExpected Output: \n", json.dumps(expected_output, indent=4))

        if parsed_data == expected_output:
            print("Match\n\n")


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