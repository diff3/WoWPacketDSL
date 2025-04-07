#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class StructInterPreter:

    @staticmethod
    def parser(lines, i):
        try:
            field_name, field_type = lines[i].split(":")
            return field_name.strip(), field_type.strip()
        except ValueError as e:
            print(f"Value error: {e}")
            print(lines[i])
        except IndexError as e:
            print(f"Index error: {e}")
            print(lines[i])