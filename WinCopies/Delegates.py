from typing import Callable

def Self(value):
    return value

def PredicateAction[T](obj: T, predicate: Callable[[T], bool], action: Callable[[T], None]) -> bool:
    if predicate(obj):
        action(obj)

        return True
    
    return False
def GetPredicateAction[T](predicate: Callable[[T], bool], action: Callable[[T], None]) -> Callable[[T], bool]:
    return lambda obj: PredicateAction(obj, predicate, action)

def BoolFuncAction(func: Callable[[], bool], action: Callable[[], None]) -> bool:
    if func():
        action()

        return True
    
    return False
def GetBoolFuncAction(func: Callable[[], bool], action: Callable[[], None]) -> Callable[[], bool]:
    return lambda: BoolFuncAction(func, action)



def __GetPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool], converter: Callable[[T, Callable[[T], bool], Callable[[T], bool]], bool]) -> Callable[[T], bool]:
    return lambda obj: converter(obj, p1, p2)

def PredicateAndAlso[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return p1(obj) and p2(obj)
def GetAndAlsoPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateAndAlso)

def PredicateAnd[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return p1(obj) & p2(obj)
def GetAndPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateAnd)

def PredicateOrElse[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return p1(obj) or p2(obj)
def GetOrElsePredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateOrElse)

def PredicateOr[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return p1(obj) | p2(obj)
def GetOrPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateOr)

def PredicateNotAndAlso[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return (not p1(obj)) and p2(obj)
def GetNotAndAlsoPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateNotAndAlso)

def PredicateNotAnd[T](obj: T, p1: Callable[[T], bool], p2: Callable[[T], bool]) -> bool:
    return (not p1(obj)) & p2(obj)
def GetNotAndPredicate[T](p1: Callable[[T], bool], p2: Callable[[T], bool]) -> Callable[[T], bool]:
    return __GetPredicate(p1, p2, PredicateNotAnd)

def PredicateNot[T](obj: T, predicate: Callable[[T], bool]) -> bool:
    return not predicate(obj)
def GetNotPredicate[T](predicate: Callable[[T], bool]) -> Callable[[T], bool]:
    return lambda obj: PredicateNot(obj, predicate)



def GetIndexedValueIndexComparison[T](index: int) -> Callable[[T], bool]:
    return lambda i, value: i == index

def GetIndexedValueValueComparison[T](value: T) -> Callable[[T], bool]:
    return lambda i, _value: value == _value

def GetIndexedValueComparison[T](index: int, value: T) -> Callable[[T], bool]:
    return lambda i, _value: i == index and value == _value