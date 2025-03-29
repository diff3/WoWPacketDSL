#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils


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