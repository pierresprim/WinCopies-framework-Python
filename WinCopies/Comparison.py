from enum import Flag

from WinCopies.Enum import HasFlag
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsRichComparison

class Closed(Flag):
    Null = 0
    Left = 1
    Right = 2
    Both = Left|Right

def __Check(x: SupportsRichComparison, y: SupportsRichComparison, b: bool) -> bool:
    return (x <= y) if b else (x < y)
def __CheckBound(x: SupportsRichComparison, y: SupportsRichComparison, b: Closed, f: Closed) -> bool:
    return __Check(x, y, HasFlag(b, f))

def Between[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(x, value, bx) and __Check(value, y, by)
def Outside[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(value, x, bx) or __Check(y, value, by)

def IsBetween[T: SupportsRichComparison](x: T, value: T, y: T, b: Closed = Closed.Both) -> bool:
    return __CheckBound(x, value, b, Closed.Left) and __CheckBound(value, y, b, Closed.Right)
def IsOutside[T: SupportsRichComparison](x: T, value: T, y: T, b: Closed = Closed.Both) -> bool:
    return __CheckBound(value, x, b, Closed.Left) or __CheckBound(y, value, b, Closed.Right)

def Equals(x: SupportsEqualityComparison, y: SupportsEqualityComparison) -> bool:
    return x == y

def CompareFrom(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x < y
def CompareTo(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x > y