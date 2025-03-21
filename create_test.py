#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class FileHandler:

    @staticmethod
    def save_bin_file(version, filename, data):
        with open(f'build/{version}/bin/{filename}.bin', "wb") as f:
            f.write(data)

    @staticmethod
    def save_def_file(version, filename, data):
        with open(f'build/{version}/def/{filename}.def', "w") as f:
            f.write(data)
    
    @staticmethod
    def save_json_file(version, filename, data):
        with open(f'build/{version}/json/{filename}.json', "w") as f:
            f.write(data)


version = 18414
opkode = "LOGIN_REALM_S"
raw_data  = b'\x10,\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00Azarim\x00192.168.11.30:8085\x00\x00\x00\x00\x00\x01\x01\x01\x10\x00'

FileHandler.save_bin_file(version, opkode, raw_data)
FileHandler.save_def_file(version, opkode, "endian: little\nheader:\ndata:\n")
FileHandler.save_json_file(version, opkode, "{}")