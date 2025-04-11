#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils
from utils.parseUtils import get_values
from modules.context import get_context


class BlockInterPreter:
    
    @staticmethod
    def parser(lines, i): 
        result = ParsingUtils.count_size_of_block_structure(lines, i)
        num = result[0]
        block_lines = result[1]
        debug = False



        loop_match = re.match(r"block\s+€(\w+):", lines[i].strip())

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


    @staticmethod
    def include_handler():
        from main import WoWStructParser
        
        ctx = get_context()
        fields, block, i, offset = ctx.get_values("fields", "block", "i", "offset")

        # Läs field entry: ("include", "€blockname")
        field_type = fields[i][1]  # ex: "€test"

        # Matcha €blockname
        match = re.match(r"^€(\w+)$", field_type)
        if not match:
            raise ValueError(f"Invalid include syntax: '{field_type}'")

        block_name = match.group(1)

        if block_name not in block:
            raise KeyError(f"Block '{block_name}' not found in ctx.block.")

        loop_ctx = ctx.clone()
        loop_ctx.fields = block[block_name]
        loop_ctx.offset = offset
        loop_ctx.i = 0
        loop_ctx.parsed_data = {}



        # Kör tolkning av det inkluderade blocket
        parsed_data, offset = WoWStructParser.extract_data(ctx=loop_ctx)

        # Uppdatera det globala parsed_data med det från blocket
        ctx.parsed_data.update(parsed_data)

        ctx.i = i
        ctx.offset = offset

        # Debug
        print(f"[include_handler] Included block '{block_name}' →", parsed_data)
