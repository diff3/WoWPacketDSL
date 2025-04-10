#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils, get_values

class LoopInterPreter:

    @staticmethod
    def parser(lines: list, i: int) -> tuple:
        """
        Parses a loop definition from the given lines, calculates the number of iterations, 
        and returns the loop details including the loop count variable, field name, and 
        the number of lines in the loop block.
        """
        
        result = ParsingUtils.count_size_of_block_structure(lines, i)
        num = result[0]
        # block_lines = result[1]
        
        loop_match = re.match(r"loop <(.*?)> as <(\w+)>:", lines[i].strip())

        if loop_match:
            loop_count_variable = loop_match.group(1)
            field_name = loop_match.group(2)

        loop_match = re.match(r"loop (\d+) as <(\w+)>:", lines[i].strip())

        if loop_match:
            loop_count_variable = loop_match.group(1)
            field_name = loop_match.group(2)

        return ("loop", loop_count_variable, field_name ,num)

    @staticmethod
    def extractor(parameters: dict) -> dict:
        from main import WoWStructParser

        fields, raw_data, debug, offset, parsed_data, i = get_values(parameters, "fields", "raw_data", "debug", "offset", "parsed_data", "i")

        _, field_type, variable_name, loop_field = fields[i]

        loop = int(parsed_data[field_type])             
        loop_fields = fields[i + 1:i + 1 + int(loop_field)]

        variable_list = []

        for x in range(loop):
            if debug:
                print(f'Loop {x}')
            
            loop_parameters = parameters.copy()
            loop_parameters.update({'fields': loop_fields, 'offset': offset, 'just': 4, 'i': 0, 'parsed_data': {}})

            parsed_loop, offset = WoWStructParser.extract_data(loop_parameters)

            variable_list.append(parsed_loop)

            if offset > len(raw_data):
                break
        
        i += len(loop_fields) + 1
        parameters["parsed_data"][variable_name] = variable_list

        parameters.update({
            "i": i,
            "offset": offset
        })

        return parameters
        
        