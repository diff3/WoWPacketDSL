#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils, get_values

from modules.context import get_context

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

        line = lines[i].strip()

        # Match: loop <number or variable> to €<target>
        loop_match = re.match(r"loop\s+(?:€)?(\w+)\s+to\s+€(\w+)", line)

        if loop_match:
            loop_count_variable = loop_match.group(1)  # string, may be digit or variable
            field_name = loop_match.group(2)          # target name (always a variable)

            return ("loop", loop_count_variable, field_name, num)

        # If no match, raise error or fallback as needed
        raise ValueError(f"Invalid loop syntax: {line}")

    @staticmethod
    def extractor():
        from main import WoWStructParser

        ctx = get_context()
        fields, raw_data, debug, offset, parsed_data, i = ctx.get_values("fields", "raw_data", "debug", "offset", "parsed_data", "i")

        _, field_type, variable_name, loop_field = fields[i]

        loop = int(parsed_data[field_type])             
        loop_fields = fields[i + 1:i + 1 + int(loop_field)]

        variable_list = []

        for x in range(loop):
            if debug:
                print(f'Loop {x}')
            
            loop_ctx = ctx.clone()
            loop_ctx.fields = loop_fields
            loop_ctx.offset = offset
            loop_ctx.just = 4
            loop_ctx.i = 0
            loop_ctx.parsed_data = {}

            parsed_loop, offset = WoWStructParser.extract_data(ctx=loop_ctx)

            variable_list.append(parsed_loop)

            if offset > len(raw_data):
                break
        
        i += len(loop_fields) + 1

        ctx.i = i
        ctx.offset = offset
        ctx.parsed_data[variable_name] = variable_list