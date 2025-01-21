# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 05:25:00 2025

@author: Pierre Sprimont
"""

def Between(x: int, value: int, y: int, bx: bool, by: bool) -> bool:
    def check(x: int, y: int, b: bool) -> bool:
        return x <= y if b else x < y
    
    return check(x, value, bx) and check(value, y, by)
def Outside(x: int, value: int, y: int, bx: bool, by: bool) -> bool:
    def check(x: int, y: int, b: bool) -> bool:
        return y <= x if b else y < x
    
    return check(x, value, bx) or check(value, y, by)