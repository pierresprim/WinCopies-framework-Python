def Self(value):
    return value

def PredicateAction(obj: object, predicate: callable, action: callable) -> bool:
    if predicate(obj):
        action(obj)

        return True
    
    return False

def GetPredicateAction(predicate: callable, action: callable) -> callable:
    return lambda obj: PredicateAction(obj, predicate, action)

def GetIndexedValueIndexComparison(index: int) -> callable:
    return lambda i, _value: index == i

def GetIndexedValueValueComparison(value) -> callable:
    return lambda i, _value: value == _value

def GetIndexedValueComparison(index: int, value) -> callable:
    return lambda i, _value: index == i and value == _value