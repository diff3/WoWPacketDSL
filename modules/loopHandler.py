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
    def extractor(field_type, parsed_data, loop_field, fields, debug ):

        try:
            loop = int(field_type)
        except ValueError:
            loop = int(parsed_data[field_type])                 

        n = i + 1
        loop_fields = fields[n:n + int(loop_field)]
        print(type(loop_field))
        variable_list = []
        for x in range(loop):
            if debug:
                print(f'Loop {x}')
            parsed_loop, offset = WoWStructParser.extract_data(raw_data, endianess, loop_fields, metadata, block, offset, just=4, debug=False)
            variable_list.append(parsed_loop)

            if offset > len(raw_data):
                break
        
        i += len(loop_fields) + 1
        parsed_data[variable_name] = variable_list

        return variable_name, variable_list,  len(loop_fields) + 1