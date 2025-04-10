#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from utils.parseUtils import ParsingUtils
from utils.parseUtils import get_values



class BlockInterPreter:
    
    @staticmethod
    def parser(lines, i): 
        result = ParsingUtils.count_size_of_block_structure(lines, i)
        num = result[0]
        block_lines = result[1]
        debug = False

        loop_match = re.match(r"block <(\w+)>:", lines[i].strip())

        variable_list = []

        if loop_match:
            variable = loop_match.group(1)

            for b in block_lines:
                try:
                    field_name, field_type = b.split(":")
                    variable_list.append((field_name.strip(), field_type.strip()))
                    num += 1
                except ValueError as e:
                    if debug:
                        print(f"Value error: {e}")
                        print(lines[i])

            return variable, variable_list, num
        
        return None


    @staticmethod
    def include_handler(parameters: dict) -> dict:
        from main import WoWStructParser
        fields, block, i, offset = get_values(parameters, "fields", "block", "i", "offset")

        # Extrahera fältets namn
        field_name = fields[i][0]

        # Försök hitta inkluderingsmönster, t.ex. <LoopName>
        pattern = r'<(.*?)>'
        match = re.search(pattern, field_name)
        if not match:
            raise ValueError(f"Fältet '{field_name}' matchade inte förväntat <name>-mönster.")

        key = match.group(1)
        if key not in block:
            raise KeyError(f"Nyckeln '{key}' finns inte i blocket.")

        # Bygg upp nya parameters för inkluderad loop
        include_parameters = parameters.copy()
        include_parameters.update({
            'fields': block[key],
            'parsed_data': {},
            'i': 0
        })

        # Kör extraktion
        parsed_loop, offset = WoWStructParser.extract_data(include_parameters)

        # Uppdatera index (vi räknar med en rad per iteration + loopen)
        i += len(parsed_loop) + 1

        # Debugutskrift
        print(f"[include_handler] Parsed loop ({key}): {parsed_loop}")

        # Uppdatera ursprungliga parametrar
        parameters['parsed_data'].update(parsed_loop)
        parameters.update({
            "i": i,
            "offset": offset
        })

        return parameters