#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import struct
import re
import json
from modules.modifierHandler import ModifierInterPreter
# from modules.bitsHandler import BitInterPreter 
from modules.context import get_context

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
            line = lines[i]
            line_content = line.strip()

            if len(line_content) <= 0:
             
                break

            # Stoppa om vi backar ut på indraget
            if len(re.match(r"^\s*", line)[0]) <= leading_spaces:
   
                break

            block_lines.append(line_content)
            ant += 1
            i += 1

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
            "i": 0,
            "bit_pos": 0,
            "byte_pos": 0
        }

    @staticmethod
    def init_parameters_new():
        ctx = get_context()
        ctx.reset()

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
            elif line.startswith("header:") or line.startswith("data:") or not line.strip():
                i += 1  
                continue  
            else:
                new_list.append(list_struct_definition[i])
                i += 1

        return new_list

    @staticmethod
    def resolve_string_field_type(field_type: str, raw_data: bytes, offset: int) -> str:
        """
        Resolves special string-related field types:

        - €len's: Dynamically sized strings based on a parsed variable or block value
        - S: Null-terminated string, size determined from raw_data
        """

        # Resolve dynamic field types using full parameter context
        field_type = resolve_euro(field_type)

        # Handle 'S' (null-terminated string)
        if field_type == 'S':
            string_data = raw_data[offset:].split(b'\x00')[0]
            length = len(string_data) + 1  # Include the null terminator
            field_type = f"{length}s"

        return field_type

    @staticmethod   
    def evaluate_slice_expression(expr: str, parsed_data: dict, raw_data: bytes) -> bytes:
        """
        Evaluates slicing expressions in the form:
        €start:€base+€offset
        €start:€base-€offset

        Returns raw_data[start:end]
        """
        match = re.match(r"^€(\w+):€(\w+)([+-])€(\w+)$", expr.strip())
        if not match:
            raise ValueError(f"Invalid slice expression: {expr}")

        start_var, base_var, operator, offset_var = match.groups()

        start = resolve_euro(f"€{start_var}", parsed_data)
        base = resolve_euro(f"€{base_var}", parsed_data)
        offset = resolve_euro(f"€{offset_var}", parsed_data)

        if not all(isinstance(x, int) for x in (start, base, offset)):
            raise TypeError("Slice operands must resolve to integers")

        end = base + offset if operator == "+" else base - offset

        return raw_data[start:end]

    @staticmethod
    def extract_struct_field(field_name, field_type, raw_data, offset, modifiers, endianess, parsed_data) -> tuple:
        """
        Extracts a field from raw_data using struct or slice expressions.

        Returns:
        - value (bytes, int, str, etc.)
        - size in bytes
        - format description (e.g., '2s', 'raw_slice')
        """
        mods = modifiers.get(field_name, [])

        # Handle raw slice expression like €start:€base+€offset
        if re.match(r"^€\w+:\€\w+[+-]€\w+$", field_type):
            value = ParsingUtils.evaluate_slice_expression(field_type, parsed_data, raw_data)
            return value, len(value), "raw_slice"

        # Override endianess from modifiers
        if ">" in mods:
            endianess = ">"
        elif "<" in mods:
            endianess = "<"

        fmt = f"{endianess}{field_type}"
        field_size = struct.calcsize(fmt)

        # Handle string
        if 's' in field_type:
            field_value = struct.unpack_from(fmt, raw_data, offset)[0]
            field_value = ModifierInterPreter.to_string_from_bytes(field_value)

        # Handle compound format (e.g. '4B')
        elif re.match(r'^\d+[A-Za-z]$', field_type):
            field_value = struct.unpack_from(fmt, raw_data, offset)

        # Handle combined values with modifier C
        elif 'C' in mods and len(fmt) > 2:
            field_value = struct.unpack_from(fmt, raw_data, offset)

        # Default: single value
        else:
            field_value = struct.unpack_from(fmt, raw_data, offset)[0]

        return field_value, field_size, fmt
    
    @staticmethod   
    def apply_modifiers(field_name: str, field_value, modifiers: dict, field_type: str = ""):
        ctx = get_context()

        if field_name not in modifiers:
            return field_value 

        bit_context = {
            "raw_data":  ctx.raw_data,
            "byte_pos": ctx.byte_pos,
            "bit_pos": ctx.bit_pos
        }

        value, byte_pos, bit_pos = ModifierInterPreter.modifier_handler(
            field_name, field_value, field_type, modifiers, bit_context
        )

        ctx.byte_pos = byte_pos
        ctx.bit_pos = bit_pos

        return value
    
    @staticmethod   
    def resolve_euro(expr: str):
        """
        Resolves €-based expressions from parsed_data and block.

        Supports:
        - €var
        - €var's
        - €var'B
        """
        
        ctx = get_context()
        parsed_data = ctx.parsed_data
        block = ctx.block

        # parsed_data = parameters.get("parsed_data", {})
        # block = parameters.get("block", {})

        if not isinstance(expr, str):
            return expr  # already a value

        if not expr.startswith("€"):
            return expr  # raw literal

        # €var's or €var'B
        match = re.match(r"^€(\w+)'([a-zA-Z])$", expr)
        if match:
            key, suffix = match.groups()
            if key in parsed_data:
                return f"{parsed_data[key]}{suffix}"
            elif key in block:
                return f"{block[key]}{suffix}"
            else:
                raise KeyError(f"Variable '€{key}' not found in parsed_data or block")

        # €var
        key = expr[1:]
        if key in parsed_data:
            return parsed_data[key]
        elif key in block:
            return block[key]

        raise KeyError(f"Variable '€{key}' not found in parsed_data or block")
    
    @staticmethod   
    def format_json_inline_list(data: list[list]) -> str:
        """
        Formats a list of lists as JSON with one inline row per item.

        Example:
        [
        ["cmd", "B"],
        ["size", "H"]
        ]
        """
        if isinstance(data, dict):
            # Convert dict to list of [key, value]
            items = [[k, v] for k, v in data.items()]
        else:
            items = list(data)

        lines = [json.dumps(item) for item in items]
        return "[\n  " + ",\n  ".join(lines) + "\n]"

    @staticmethod
    def check_endian(line):
        endian_type = line.split(":")[1].strip()
        return "<" if endian_type == "little" else ">"
  
        

get_values = ParsingUtils.get_values
apply_modifiers = ParsingUtils.apply_modifiers
extract_struct_field = ParsingUtils.extract_struct_field
resolve_euro = ParsingUtils.resolve_euro
count_size_of_block_structure = ParsingUtils.count_size_of_block_structure
format_json_inline_list = ParsingUtils.format_json_inline_list