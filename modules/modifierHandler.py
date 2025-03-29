#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class ModifierOperator:

    @staticmethod
    def modifier_parser(line:str, metadata:dict, fields:list):
        """
        Parses a line containing a field definition and updates the metadata and fields lists.

        The method splits the line into field name, field type, and modifiers, then updates the 
        metadata dictionary with the modifiers associated with the field. It also appends the 
        field name and type to the fields list.

        Return metadata dict, and fields list
        """

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
        """
        Applies modifiers to a field value based on the field's name, type, and associated metadata.

        This method first checks if the field's value is of type `bytes` and if the field type is a string (`s`).
        It then decodes the bytes to a string (if possible), or converts it to a hexadecimal string. 
        Next, it applies the modifiers from the metadata to the field value using a mapping of modifier operations.
        """
        
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
            try:
                field_value = field_value.decode("utf-8").strip("\x00")
            except UnicodeDecodeError:
                field_value = field_value.hex()

        return field_value            


modifiers_opereration_mapping = {
    "H": ModifierOperator.to_hex,
    "M": ModifierOperator.to_mirror,
    "s": ModifierOperator.to_string,
    "u": ModifierOperator.to_lower,
    "U": ModifierOperator.to_upper,
    "W": ModifierOperator.to_ip_address
}