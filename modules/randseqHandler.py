#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils, get_values, resolve_euro
from modules.bitsHandler import BitInterPreter
from modules.context import get_context

class RandseqInterPreter:

    @staticmethod
    def parser(lines, i): 

        result = ParsingUtils.count_size_of_block_structure(lines, i)

        num = result[0]
        # block_lines = result[1]
        
        line = lines[i].strip()
        # loop_match = re.match(r"randseq (\d+) as <(\w+)>:", lines[i].strip())
        match = re.match(r"randseq\s+(?:€)?(\w+)\s+as\s+€(\w+)", line)


        if match:
            length_in_bytes = match.group(1)
            variable_name = match.group(2)
        
            return ("randseq", length_in_bytes, variable_name, num)

        return None

    @staticmethod
    def extractor():
        ctx = get_context()
        fields, raw_data, offset, parsed_data, i = ctx.get_values("fields", "raw_data", "offset", "parsed_data", "i")

        field_type = fields[i][1]
        loop = int(field_type)
        len_raw_data = len(raw_data)

        # Fälten efter 'randseq ...' blocket
        n = i + 1
        raw_randseq_fields = fields[n:n + loop]

        randseq_definition = {}

        # Dela upp varje fält i namn och värde
        for raw_field in raw_randseq_fields:
            print(raw_field)
            if isinstance(raw_field, str):
                if ':' not in raw_field:
                    continue  # eller raise ValueError
                field_name, value = raw_field.split(":", 1)
            elif isinstance(raw_field, tuple):
                field_name, value = raw_field
            else:
                raise TypeError(f"Unexpected field format: {raw_field}")

            field_name = field_name.strip()
            value = value.strip()

            # Hantering enligt din DSL
            if " " in value and not any(op in value for op in "-:+*/"):
                parts = [int(x) for x in value.split()]
                randseq_definition[field_name] = parts

            elif "-" in value and not value.startswith("€"):
                start, end = map(int, value.split("-"))
                randseq_definition[field_name] = (start, end)

            elif value.isdigit():
                randseq_definition[field_name] = int(value)

            elif value.startswith("€"):
                randseq_definition[field_name] = resolve_euro(value, parsed_data)

            else:
                raise ValueError(f"Unknown value format in randseq: {value}")


        parsed_data_randseq = {}

        for key, value in randseq_definition.items():
            if isinstance(value, list):  # Om det är en lista av bytes
                parsed_data_randseq[key] = [f"{raw_data[index]:02X}" for index in value]
                parsed_data_randseq[key] = "".join(parsed_data_randseq[key])
            
            elif isinstance(value, tuple):  # Om det är en tuple av start och slut position
                start, end = value
                parsed_data_randseq[key] = int.from_bytes(raw_data[int(start):int(end)], byteorder='little')
        
        addon_size = int.from_bytes(raw_data[54:58], byteorder='little')
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
    
        # i += len(loop_fields) + 1

        i += int(loop) + 1
        offset += len_raw_data

        ctx.i = i
        ctx.offset = offset