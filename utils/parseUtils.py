#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re


class ParsingUtils:
    
    @staticmethod
    def count_size_of_block_structure(lines: list, i: int) -> list:
        """
        Given a list of lines and a starting index, this function returns the number of 
        indented lines and the list of those lines within the loop.
        """

        block_lines = []
        leading_spaces = len(re.match(r"^\s*", lines[i])[0])

        i += 1
        ant = 0

        while i < len(lines):
            line = lines[i].strip()

            if len(re.match(r"^\s*", lines[i])[0]) > leading_spaces:
                block_lines.append(line)  
                ant += 1
                i += 1 
            else:
                break

        return [ant, block_lines]

    @staticmethod   
    def remove_comments_and_reserved(struct_definition):
        """
        Removes comments (single and multi-line) and reserved sections ('header:', 'data:') 
        from the provided structure definition.
        """

        list_struct_definition = struct_definition.split('\n')
        i = 0
        new_list = []

        while i < len(list_struct_definition):
            line = list_struct_definition[i].strip()

            if line.startswith('#-'):
                while not list_struct_definition[i].strip().endswith("-#"):
                    i += 1  
                i += 1  
                continue  
            elif line.startswith('#'):
                i += 1  
                continue 
            elif '#' in line:
                line = list_struct_definition.split('#')[0].strip()
                if line:  
                    new_list.append(line)
                i += 1
                continue  
            elif line.startswith("header:") or line.startswith("data:"):
                if line == "header:" or line == "data:":
                    i += 1  
                    continue  
            else:
                new_list.append(list_struct_definition[i])
                i += 1

        return new_list