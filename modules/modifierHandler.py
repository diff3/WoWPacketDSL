#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import struct
import re
from modules.bitsHandler import BitInterPreter


class ModifierInterPreter:

    @staticmethod
    def parser(line:str, metadata:dict, fields:list):
        """
        Parses a line containing a field definition and updates the metadata and fields lists.

        The method splits the line into field name, field type, and modifiers, then updates the 
        metadata dictionary with the modifiers associated with the field. It also appends the 
        field name and type to the fields list.

        Return metadata dict, and fields list
        """
      
        field_name, field_type = line.split(":")
        field_type, metadata_info = field_type.split(",")

        mods = []

        for raw_mod in metadata_info.strip().split(','):
            mod = raw_mod.strip()
            i = 0
            while i < len(mod):
                # Match t.ex. 7B, 3B, B
                match = re.match(r'(\d*)(B)', mod[i:])
                if match:
                    num, letter = match.groups()
                    mods.append(f"{num}{letter}" if num else letter)
                    i += match.end()
                else:
                    # Enstaka bokstav (modifier), eller bokstav efter siffra (t.ex. 8X → X)
                    if mod[i].isalpha() or mod[i] in "<>":
                        mods.append(mod[i])
                    # ignorera siffror om de inte tillhör en B-modifier
                    i += 1

        if mods:
            metadata[field_name.strip()] = mods

        fields.append((field_name.strip(), field_type.strip()))
        return metadata, fields


    @staticmethod
    def modifier_handler(field_name, field_value, field_type, metadata, bit_context=None):
        """
        Applies modifiers to a field value based on the field's name, type, and associated metadata.

        This method first checks if the field's value is of type `bytes` and if the field type is a string (`s`).
        It then decodes the bytes to a string (if possible), or converts it to a hexadecimal string. 
        Next, it applies the modifiers from the metadata to the field value using a mapping of modifier operations.
        """
        
        byte_pos = 0
        bit_pos = 0

        if isinstance(field_value, bytes) and ("s" in field_type) and not ('ip' in field_name):
            try:
                field_value = field_value.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                field_value = field_value.hex()


        for modifier in metadata.get(field_name, []):

            if modifier.endswith("B"):
                if bit_context is None:
                    raise ValueError(f"Bit modifier '{modifier}' requires bit_context with raw_data, byte_pos, and bit_pos")

                num_bits = int(modifier[:-1]) if len(modifier) > 1 else 1

                field_value, byte_pos, bit_pos = modifiers_opereration_mapping["B"](
                    bit_context["raw_data"],
                    bit_context["byte_pos"],
                    bit_context["bit_pos"],
                    num_bits
                )

                bit_context["byte_pos"] = byte_pos
                bit_context["bit_pos"] = bit_pos

            elif modifier in modifiers_opereration_mapping:
                field_value = modifiers_opereration_mapping[modifier](field_value)

        return field_value, byte_pos, bit_pos

    @staticmethod
    def combine_data(field_value):
        combined = 0

        for value in field_value:
            combined += value

        return combined
    
    @staticmethod
    def to_capitalized(value):
        if isinstance(value, str):
            return value.capitalize()
        return value
    
    @staticmethod
    def to_int(field_value):
        """
        Converts a list of bits to an integer. If already an int, return as-is.
        """
        if isinstance(field_value, list):
            return int(''.join(str(v) for v in field_value), 2)

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
        elif isinstance(field_value, str):
            try:
                byte_data = bytes.fromhex(field_value)
                return ".".join(str(b) for b in byte_data)
            except ValueError:
                print(f"Invalid hex value: {field_value}")
                return None

        return field_value 
    
    @staticmethod
    def to_trimmed(value):
        if isinstance(value, str):
            return value.strip()
        return value

    @staticmethod
    def to_string(field_value):
        if isinstance(field_value, str): 
            return field_value.decode("utf-8").strip("\x00")
        return field_value
    
    @staticmethod
    def to_string_from_bytes(field_value):
        if isinstance(field_value, bytes):
            try:
                field_value = field_value.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                field_value = field_value.hex()

        return field_value      


modifiers_opereration_mapping = {
    "B": BitInterPreter.from_bits,
    "C": ModifierInterPreter.combine_data,
    "H": ModifierInterPreter.to_hex,
    "I": ModifierInterPreter.to_int,
    "M": ModifierInterPreter.to_mirror,
    "N": ModifierInterPreter.to_capitalized,
    "U": ModifierInterPreter.to_upper,
    "W": ModifierInterPreter.to_ip_address,
    "s": ModifierInterPreter.to_string,
    "t": ModifierInterPreter.to_trimmed,
    "u": ModifierInterPreter.to_lower,
}