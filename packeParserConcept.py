#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import struct


""" 
The WoWStruct format defines the structure of network packets, where each field is
described by a format code (e.g., B for a byte, I for an unsigned int) and associated
metadata (e.g., mirroring, IP conversion). The parser reads this structure definition,
handles dynamic fields, applies transformations based on metadata (e.g., mirroring or 
converting to uppercase), and extracts the corresponding data from raw binary. 
This flexible approach allows efficient parsing of WoW network packets, 
with support for variable-length fields and custom modifications.


Modifiers:

M: mirrored (Reverses the byte order for strings or data)
W: ip (Converts byte data into a properly formatted IP address)
U: uppercase (Converts string data to uppercase)
u: lowercase (Converts string data to lowercase)
endian: little, big (Defines byte order for multi-byte fields)
  
Common struct Format:

B: unsigned char (1 byte)
b: signed char (1 byte)
H: unsigned short (2 bytes,)
h: signed short (2 bytes)
I: unsigned int (4 bytes)
i: signed int (4 bytes)
L: unsigned long (4 bytes)
l: signed long (4 byte)
Q: unsigned long long (8 bytes)
q: signed long long (8 bytes)
f: float (4 bytes, 32-bit)
d: double (8 bytes, 64-bit)
s: string (Used for specifying byte-length strings, e.g., 4s for a 4-byte string)
p: pascal string (A string where the first byte indicates the string length)
P: pointer (A system-dependent pointer to an object, typically for C pointers)
x: pad byte (Fills with 0x00 to adjust byte boundaries)
?: boolean (1 byte, True or False)
"""


AUTH_LOGON_CHALLENGE_C = """
    endian: little
    header:
    data:
        cmd: B
        error: B
        size: H
        gamename: 4s, M
        version1: B
        version2: B
        version3: B
        build: H
        platform: 4s, M
        os: 4s, M
        country: 4s, M
        timezone_bias: I
        ip: 4s, W
        I_len: B
        dynamic I_len:
            I: s """


CLIENTCACHE_VERSION = """
    endian: little
    header: 
    data:
        version: B """


AUTHLOGONCHALLENGES = """
    cmd: B
    error: B
    success: B
    B: 32s, MU
    l: B
    g: B
    blog: B
    N: 32s, MU
    s: 32s, MU
    unk3: 16s, MU
    securityFlags: B """


AUTHLOGONPROOFSERVER = """
    cmd: B
    error: B
    M2: 20s, U
    unk1: I
    unk2: I
    unk3: H """


class WoWStructParser:
    """ 
    The WoWStructParser class is used to define and parse network packet structures (WoW-Struct format). 
    It reads the structure definition, handles dynamic fields, and applies the appropriate transformations 
    such as endianess, string mirroring, and IP formatting.
    """

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

            if "dynamic" in line:
                _, value = line[:-1].split(" ")

                i += 1

                field_name, field_type = lines[i].split(":")

                if value:
                    dynamic_fields[field_name.strip()] = value.strip() 
                    fields.append((field_name.strip(), field_type.strip()))
                else:
                    print(f"Fel: Dynamisk längd saknas för {field_name}")

                i += 1
                continue 

            if ":" in line and "," in line:
                field_name, field_type = line.split(":")
                field_type, metadata_info = field_type.split(",")

                s = ''.join(metadata_info.strip().split(','))

                if len(s) > 1:
                    for char in s:
                        # print(char)
                        char = char.strip()
                        if field_name.strip() in metadata:
                            metadata[field_name.strip()].append(char)
                        else:
                            metadata[field_name.strip()] = [char]
                else:
                    metadata[field_name.strip()] = [metadata_info.strip()]
                
                fields.append((field_name.strip(), field_type.strip()))
            
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
            if field_name in dynamic_fields:
                length_field = dynamic_fields[field_name]
                length = parsed_data[length_field]  
                fmt = f"{endianess}{length}s"  
            else:
                fmt = f"{endianess}{field_type}" 

            field_size = struct.calcsize(fmt)
            field_value = struct.unpack_from(fmt, raw_data, offset)[0]
            offset += field_size

            if field_name in metadata:
                for meta in metadata[field_name]:
                    if meta == "W" and isinstance(field_value, bytes):
                        field_value = ".".join(str(b) for b in field_value)

                    if isinstance(field_value, bytes) and "s" in field_type:
                        try:
                            field_value = field_value.decode("utf-8").strip("\x00")
                        except UnicodeDecodeError:
                            field_value = field_value.hex()

                    if meta == "M":
                        field_value = field_value[::-1]
                    elif meta == "U":
                        field_value = field_value.upper()
                    elif meta == "u":
                        field_value = field_value.lower()
                
                parsed_data[field_name] = field_value

            else:
                if isinstance(field_value, bytes) and "s" in field_type:
                    try:
                        field_value = field_value.decode("utf-8").strip("\x00")
                    except UnicodeDecodeError:
                        field_value = field_value.hex()

                parsed_data[field_name] = field_value

        return parsed_data


if __name__ == "__main__":

    # Test data:

    raw_data1 = b'\x08\x00\x34\x00WoW\x00\x05\x04\x08\xeeG68x\x00niW\x00BGne<\x00\x00\x00\xc0\xa8\x0b\x1e\x04MAPE'
    raw_data2 = b'\x05\x00\x00\x00'
    raw_data3 = b'\x00\x00\x00\x13r\x1bS\xbf\r<e*N\xd0\x03v\x19\x94G\x1a/\x99\x1e#\n\xa3KGbei\xff\x8dN\x1d\x01\x07 \xb7\x9b>*\x87\x82<\xab\x8f^\xbf\xbf\x8e\xb1\x01\x08SP\x06)\x8b[\xad\xbd[S\xe1\x89^dK\x89<\xddhrM\xc9l\x05<\xf7*\xad/0_g\x93;?m6[qQ\xfd\xf5c<\xc8\xf3\xdd\x13\xa0\x02\xe1hJ\xd2R\x18\xfe\xd7,\x1b\x90\x17\x9e\xd3\x00'
    raw_data4 = b'\x00\xe7\x0f\x83,EK\x15S\x1cL+\xe7\x01 \x87u\x8e\x03\xb7&\x03\x93\x1e\x9b\xc7\xa7\x8b\ry\x89\xf5\x07\xecR<\x90\xc9\xfeo\xe2X\x1d\x80\xe3\xfb\xc3\xee"[\xd7\t`\x82\xfb\xaaL\xd6;e\xa2\x0f\xc8\x1c\xc70\x87\x83Mh\xaa\x83\xdc\x00\x00'

    cases = {
        "1": [AUTH_LOGON_CHALLENGE_C, raw_data1],
        "2": [CLIENTCACHE_VERSION, raw_data2],
        "3": [AUTHLOGONCHALLENGES, raw_data3],
        "4": [AUTHLOGONPROOFSERVER, raw_data4],
    }

    case = "4"

    endianess, fields, dynamic_fields, metadata = WoWStructParser.parse_struct_definition(cases[case][0])
    parsed_data = WoWStructParser.extract_data(cases[case][1], endianess, fields, dynamic_fields, metadata)

    print(f'Data: \n{cases[case][1]}')
    print()
    print(f"Parsed: \n{json.dumps(parsed_data, indent=4)}")
