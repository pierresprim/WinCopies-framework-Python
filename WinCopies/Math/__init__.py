# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 05:25:00 2025

@author: Pierre Sprimont
"""

def __Check(x: int, y: int, b: bool) -> bool:
    return x <= y if b else x < y

def Between(x: int, value: int, y: int, bx: bool = True, by: bool = True) -> bool:
    return __Check(x, value, bx) and __Check(value, y, by)
def Outside(x: int, value: int, y: int, bx: bool = True, by: bool = True) -> bool:
    return __Check(value, x, bx) or __Check(y, value, by)