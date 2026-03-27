# -*- coding: utf-8 -*-
"""
Created on Tue Jan 21 05:25:00 2025

@author: Pierre Sprimont
"""

from decimal import Decimal as decimal

type NumericalValue = int|float|decimal

def __Check(x: NumericalValue, y: NumericalValue, b: bool) -> bool:
    return x <= y if b else x < y

def Between(x: NumericalValue, value: NumericalValue, y: NumericalValue, bx: bool = True, by: bool = True) -> bool:
    return __Check(x, value, bx) and __Check(value, y, by)
def Outside(x: NumericalValue, value: NumericalValue, y: NumericalValue, bx: bool = True, by: bool = True) -> bool:
    return __Check(value, x, bx) or __Check(y, value, by)

def CompareFrom(x: NumericalValue, y: NumericalValue) -> bool|None:
    return None if x == y else x < y
def CompareTo(x: NumericalValue, y: NumericalValue) -> bool|None:
    return None if x == y else x > y