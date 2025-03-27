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
opkode = "SMSG_SET_TIME_ZONE_INFORMATION"
raw_data = b'\x0e\x1cEtc/UTCEtc/UTC'

FileHandler.save_bin_file(version, opkode, raw_data)
FileHandler.save_def_file(version, opkode, "endian: little\nheader:\ndata:\n")
FileHandler.save_json_file(version, opkode, "{}")