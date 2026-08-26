from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsRichComparison

def __Check(x: SupportsRichComparison, y: SupportsRichComparison, b: bool) -> bool:
    return (x <= y) if b else (x < y)

def Between[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(x, value, bx) and __Check(value, y, by)
def Outside[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(value, x, bx) or __Check(y, value, by)

def Equals(x: SupportsEqualityComparison, y: SupportsEqualityComparison) -> bool:
    return x == y

def CompareFrom(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x < y
def CompareTo(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x > y