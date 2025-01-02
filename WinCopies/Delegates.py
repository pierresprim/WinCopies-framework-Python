from typing import Callable

from WinCopies import Predicate

def Self[T](value: T) -> T:
    return value

def BoolTrue() -> bool:
    return True
def BoolFalse() -> bool:
    return False
def FuncNone() -> None:
    return None

def PredicateAction[T](obj: T, predicate: Predicate[T], action: Callable[[T], None]) -> bool:
    if predicate(obj):
        action(obj)

        return True
    
    return False
def GetPredicateAction[T](predicate: Predicate[T], action: Callable[[T], None]) -> Predicate[T]:
    return lambda obj: PredicateAction(obj, predicate, action)

def BoolFuncAction(func: Callable[[], bool], action: Callable[[], None]) -> bool:
    if func():
        action()

        return True
    
    return False
def GetBoolFuncAction(func: Callable[[], bool], action: Callable[[], None]) -> Callable[[], bool]:
    return lambda: BoolFuncAction(func, action)



def __GetPredicate[T](p1: Predicate[T], p2: Predicate[T], converter: Callable[[T, Predicate[T], Predicate[T]], bool]) -> Predicate[T]:
    return lambda obj: converter(obj, p1, p2)

def PredicateAndAlso[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return p1(obj) and p2(obj)
def GetAndAlsoPredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateAndAlso)

def PredicateAnd[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return p1(obj) & p2(obj)
def GetAndPredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateAnd)

def PredicateOrElse[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return p1(obj) or p2(obj)
def GetOrElsePredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateOrElse)

def PredicateOr[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return p1(obj) | p2(obj)
def GetOrPredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateOr)

def PredicateNotAndAlso[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return (not p1(obj)) and p2(obj)
def GetNotAndAlsoPredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateNotAndAlso)

def PredicateNotAnd[T](obj: T, p1: Predicate[T], p2: Predicate[T]) -> bool:
    return (not p1(obj)) & p2(obj)
def GetNotAndPredicate[T](p1: Predicate[T], p2: Predicate[T]) -> Predicate[T]:
    return __GetPredicate(p1, p2, PredicateNotAnd)

def PredicateNot[T](obj: T, predicate: Predicate[T]) -> bool:
    return not predicate(obj)
def GetNotPredicate[T](predicate: Predicate[T]) -> Predicate[T]:
    return lambda obj: PredicateNot(obj, predicate)



def GetIndexedValueIndexComparison[T](index: int) -> Predicate[T]:
    return lambda i, value: i == index

def GetIndexedValueValueComparison[T](value: T) -> Predicate[T]:
    return lambda i, _value: value == _value

def GetIndexedValueComparison[T](index: int, value: T) -> Predicate[T]:
    return lambda i, _value: i == index and value == _value