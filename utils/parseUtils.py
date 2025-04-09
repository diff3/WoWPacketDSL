#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


class ParsingUtils:
    
    @staticmethod
    def count_size_of_block_structure(lines: list, i: int) -> list:
        """
        Given a list of lines and a starting index, this function returns the number of 
        indented lines and the list of those lines within the loop.
        """

        block_lines = []
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])

        i += 1
        ant = 0

        while i < len(lines):
            line = lines[i].strip()

            if len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
                block_lines.append(line)  
                ant += 1
                i += 1 
            else:
                break

        return [ant, block_lines]

    @staticmethod   
    def get_values(d: dict, *keys) -> dict:
        """
        Returns the values from the dictionary `d` corresponding to the provided keys.
        """

        return (d[k] for k in keys)
    
    @staticmethod   
    def init_parameters(raw_data, struct_definition_list, debug=False, endianess="<"):
        return {
            "endianess": endianess,
            "fields": [],
            "modifiers": {},
            "block": {},
            "raw_data": raw_data,  
            "debug": debug,
            "struct_definition_list": struct_definition_list,
            "just": 0, 
            "offset": 0,
            "parsed_data": {},
            "i": 0
        }

    @staticmethod   
    def remove_comments_and_reserved(struct_definition):
        """
        Removes comments (single and multi-line) and reserved sections ('header:', 'data:') 
        from the provided structure definition.
        """

        list_struct_definition = struct_definition.split('\n')
        i = 0
        new_list = []

        while i < len(list_struct_definition):
            line = list_struct_definition[i].strip()

            if line.startswith('#-'):
                while not list_struct_definition[i].strip().endswith("-#"):
                    i += 1  
                i += 1  
                continue  
            elif line.startswith('#'):
                i += 1  
                continue 
            elif '#' in line:
                line = list_struct_definition.split('#')[0].strip()
                if line:  
                    new_list.append(line)
                i += 1
                continue  
            elif line.startswith("header:") or line.startswith("data:"):
                if line == "header:" or line == "data:":
                    i += 1  
                    continue  
            else:
                new_list.append(list_struct_definition[i])
                i += 1

        return new_list

    def resolve_string_field_type(field_type: str, raw_data: bytes, offset: int, parsed_data: dict) -> str:
        """
        Resolves special string-related field types:
        - <variable>s: Dynamically sized strings based on a previously parsed value
        - S: Null-terminated string with unknown length, calculated from raw_data
        """

        # Replace <variable>s with the actual value from parsed_data
        if match := re.search(r'<(.*?)>s', field_type):
            variable = match.group(1)
            try:
                field_type = f"{parsed_data[variable]}s"
            except KeyError:
                raise KeyError(f"Variable '{variable}' not found in parsed_data")

        # Handle 'S' as a null-terminated string (e.g. C-style string)
        if field_type == 'S':
            string_data = raw_data[offset:].split(b'\x00')[0]
            length = len(string_data) + 1  # Include the null terminator
            field_type = f"{length}s"

        return field_type
        

get_values = ParsingUtils.get_values