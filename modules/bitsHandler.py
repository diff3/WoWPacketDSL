#!/usr/bin/env python3
# -*- coding: utf-8 -*-


class BitInterPreter:
    """
    Class to read bits from a byte array.
    """
    
    @staticmethod
    def read_bit(data: bytes, byte_pos: int, bit_pos: int) -> tuple:
        """
        Reads a single bit from the byte array and updates the byte and bit positions.
        """
        
        cur_byte = data[byte_pos]
        bit = (cur_byte >> (7 - bit_pos)) & 1
        bit_pos += 1

        if bit_pos > 7: 
            bit_pos = 0
            byte_pos += 1

        return bit, byte_pos, bit_pos

    @staticmethod
    def read_bits(data: bytes, byte_pos: int, bit_pos: int, num_bits: int) -> tuple:
        """
        Reads multiple bits from the byte array and updates the byte and bit positions.
        """
        
        value = 0

        for _ in range(num_bits):
            bit, byte_pos, bit_pos = BitInterPreter.read_bit(data, byte_pos, bit_pos)
            value = (value << 1) | bit
        
        return value, byte_pos, bit_pos