#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils


class BlockInterPreter:
    
    @staticmethod
    def parser(lines, i): 
        result = ParsingUtils.count_size_of_block_structure(lines, i)
        num = result[0]
        block_lines = result[1]

        loop_match = re.match(r"block <(\w+)>:", lines[i].strip())

        variable_list = []

        if loop_match:
            variable = loop_match.group(1)

            for b in block_lines:
                try:
                    field_name, field_type = b.split(":")
                    variable_list.append((field_name.strip(), field_type.strip()))
                    
                except ValueError as e:
                    if debug:
                        print(f"Value error: {e}")
                        print(lines[i])

            num += 1

            return variable, variable_list, num
        
        return None