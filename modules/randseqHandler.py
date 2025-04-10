#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils, get_values
from modules.bitsHandler import BitInterPreter


class RandseqInterPreter:

    @staticmethod
    def parser(lines, i): 

        result = ParsingUtils.count_size_of_block_structure(lines, i)

        num = result[0]
        block_lines = result[1]
        
        loop_match = re.match(r"randseq (\d+) as <(\w+)>:", lines[i].strip())

        if loop_match:
            length_in_bytes = loop_match.group(1)
            variable_name = loop_match.group(2)
        
            return ("randseq", length_in_bytes, variable_name, num)

        return None

    @staticmethod
    def extractor(parameters: dict) -> dict:
        fields, raw_data, debug, offset, parsed_data, i = get_values(parameters, "fields", "raw_data", "debug", "offset", "parsed_data", "i")
        print(fields[i])
        # _, field_type = fields[i]
        _, field_type, variable_name, loop_field = fields[i]

        loop = int(field_type)
        len_raw_data = len(raw_data)


        n = i + 1
        randseq_fields = fields[n:n + loop]

        randseq_definition = {}

        for field in randseq_fields:
            if not '-' in field[1] and ' ' in field[1]:
                randseq_definition[field[0]] = [int(x) for x in field[1].split(' ')]
            elif  '-' in field[1]:
                randseq_definition[field[0]] = tuple(field[1].split('-'))
            elif not '-' in field[1]:
                randseq_definition[field[0]] = field[1]
            elif '><' in field[1]:
                pattern = r'<(\w+)><(\w+)>'
                match = re.search(pattern, field[1])


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
        # parameters["parsed_data"][variable_name] = variable_list

        i += int(loop) + 1
        offset += len_raw_data


        parameters.update({
           "i": i,
           "offset": offset
        })

        return parameters
        
        