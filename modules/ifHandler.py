import re
from main import WoWStructParser
from utils.parseUtils import resolve_euro, count_size_of_block_structure


"""
if line.startswith("if "):
    info = IfInterPrePreter.parser(lines, i, parsed_data)
    parameters = IfInterPrePreter.extractor(info, parameters)
    continue

"""



class IfInterPrePreter:

    @staticmethod
    def parser(lines, i):
        line = lines[i].strip()

        match = re.match(r"^if\s+(€\w+)\s*(==|!=|>=|<=|>|<)\s*(€?\w+):$", line)
        if not match:
            raise ValueError(f"Invalid if-statement: {line}")

        left_expr, operator, right_expr = match.groups()
        if_block_len = count_size_of_block_structure(lines, i)
        else_block_len = 0

        has_else = False
        else_index = i + if_block_len + 1

        if else_index < len(lines) and lines[else_index].strip() == "else:":
            has_else = True
            else_block_len = count_size_of_block_structure(lines, else_index)

        return {
            "type": "if",
            "i": i,
            "if_len": if_block_len,
            "else_len": else_block_len,
            "has_else": has_else,
            "left_expr": left_expr,
            "right_expr": right_expr,
            "operator": operator
        }

    @staticmethod
    def evaluate(op, a, b):
        ops = {
            "==": lambda x, y: x == y,
            "!=": lambda x, y: x != y,
            ">":  lambda x, y: x > y,
            "<":  lambda x, y: x < y,
            ">=": lambda x, y: x >= y,
            "<=": lambda x, y: x <= y,
        }
        if op not in ops:
            raise ValueError(f"Unsupported operator: {op}")
        return ops[op](a, b)

    @staticmethod
    def extractor(info, parameters):
        parsed_data = parameters["parsed_data"]
        lines = parameters["lines"]

        left = resolve_euro(info["left_expr"], parsed_data)
        right = resolve_euro(info["right_expr"], parsed_data)

        condition = IfInterPrePreter.evaluate(info["operator"], left, right)

        if condition:
            block_start = info["i"] + 1
            block_end = block_start + info["if_len"]
        elif info["has_else"]:
            block_start = info["i"] + info["if_len"] + 2
            block_end = block_start + info["else_len"]
        else:
            return parameters  # no block to parse

        fields = parameters["fields"][block_start:block_end]

        sub_params = {
            **parameters,
            "fields": fields,
            "i": 0
        }

        parsed_inner, _ = WoWStructParser.extract_data(sub_params)
        parsed_data.update(parsed_inner)

        parameters["parsed_data"] = parsed_data
        parameters["i"] = info["i"] + info["if_len"] + (info["else_len"] + 1 if info["has_else"] else 1)
        return parameters