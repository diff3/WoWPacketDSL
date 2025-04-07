#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils

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


class LoopExtrator:
    
    @staticmethod
    def extractor(parameters):
        endianess, fields, metadata, block, raw_data, debug, struct_definition_list, just, offset = parameters.values()

        loop = int(parsed_data[field_type])                 
        loop_fields = fields[i + 1:i + 1 + int(loop_field)]
        variable_list = []

        for x in range(loop):
            if debug:
                print(f'Loop {x}')
            
            loop_parameters = parameters
            loop_parameters.update({'fields': loop_fields, 'offset': offset, 'just': 4})

            parsed_loop, offset = WoWStructParser.extract_data(loop_parameters)
            variable_list.append(parsed_loop)

            if offset > len(raw_data):
                break
        
        i += len(loop_fields) + 1
        parsed_data[variable_name] = variable_list