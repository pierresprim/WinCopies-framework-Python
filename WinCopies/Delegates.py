def Self(value) -> object:
    return value

def GetIndexedValueIndexComparison(index: int) -> callable:
    return lambda i, _value: index == i

def GetIndexedValueValueComparison(value) -> callable:
    return lambda i, _value: value == _value

def GetIndexedValueComparison(index: int, value) -> callable:
    return lambda i, _value: index == i and value == _value