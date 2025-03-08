from typing import Callable

from WinCopies.Typing.Delegate import Action, Function, Method, Predicate, EqualityComparison, IndexedValueComparison

def Self[T](value: T) -> T:
    return value

def BoolTrue() -> bool:
    return True
def BoolFalse() -> bool:
    return False
def FuncNone() -> None:
    return None

def CompareEquality[T](x: T, y: T) -> bool:
    return x == y

def PredicateAction[T](obj: T, predicate: Predicate[T], action: Method[T]) -> bool:
    if predicate(obj):
        action(obj)

        return True
    
    return False
def GetPredicateAction[T](predicate: Predicate[T], action: Method[T]) -> Predicate[T]:
    return lambda obj: PredicateAction(obj, predicate, action)

def BoolFuncAction(func: Function[bool], action: Action) -> bool:
    if func():
        action()

        return True
    
    return False
def GetBoolFuncAction(func: Function[bool], action: Action) -> Function[bool]:
    return lambda: BoolFuncAction(func, action)



def __CheckRepeat(n: int) -> None:
    if n < 1:
        raise ValueError()

def __RepeatAndAlso(n: int, func: Function[bool]) -> bool:
    i: int = 1

    while i < n:
        if func():
            i += 1

        return False

    return func()
def RepeatAndAlso(n: int, func: Function[bool]) -> bool:
    __CheckRepeat(n)

    match n:
        case 1:
            return func()
        case 2:
            return func() and func()
    
    return __RepeatAndAlso(n, func)
def GetRepeatAndAlso(n: int, func: Function[bool]) -> Function[bool]:
    __CheckRepeat(n)

    match n:
        case 1:
            return func
        case 2:
            return lambda: func() and func()
    
    return lambda: __RepeatAndAlso(n, func)

def __RepeatAnd(n: int, func: Function[bool]) -> bool:
    i: int = 1
    result: bool = True

    action: Action|None = None

    def loop() -> None:
        nonlocal action
        nonlocal result

        if not func():
            result = False
            action = lambda: func()
    
    action = loop

    while i < n:
        i += 1

        action()
    
    action()

    return result
def RepeatAnd(n: int, func: Function[bool]) -> bool:
    __CheckRepeat(n)

    match n:
        case 1:
            return func()
        case 2:
            return func() & func()
    
    return __RepeatAnd(n, func)
def GetRepeatAnd(n: int, func: Function[bool]) -> Function[bool]:
    __CheckRepeat(n)

    match n:
        case 1:
            return func
        case 2:
            return lambda: func() & func()
    
    return lambda: __RepeatAnd(n, func)

def __RepeatOrElse(n: int, func: Function[bool]) -> bool:
    i: int = 1

    while i < n:
        if func():
            return True

        i += 1

    return func()
def RepeatOrElse(n: int, func: Function[bool]) -> bool:
    __CheckRepeat(n)

    match n:
        case 1:
            return func()
        case 2:
            return func() or func()
    
    return __RepeatOrElse(n, func)
def GetRepeatOrElse(n: int, func: Function[bool]) -> Function[bool]:
    __CheckRepeat(n)

    match n:
        case 1:
            return func
        case 2:
            return lambda: func() or func()
    
    return lambda: __RepeatOrElse(n, func)

def __RepeatOr(n: int, func: Function[bool]) -> bool:
    i: int = 1
    result: bool = False

    action: Action|None = None

    def loop() -> None:
        nonlocal action
        nonlocal result

        if func():
            result = True
            action = lambda: func()
    
    action = loop

    while i < n:
        i += 1

        action()
    
    action()

    return result
def RepeatOr(n: int, func: Function[bool]) -> bool:
    __CheckRepeat(n)

    match n:
        case 1:
            return func()
        case 2:
            return func() | func()
    
    return __RepeatOr(n, func)
def GetRepeatOr(n: int, func: Function[bool]) -> Function[bool]:
    __CheckRepeat(n)

    match n:
        case 1:
            return func
        case 2:
            return lambda: func() | func()
    
    return lambda: __RepeatOr(n, func)



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
    return lambda obj: not predicate(obj)

def __GetFunction(f1: Function[bool], f2: Function[bool], converter: Callable[[Function[bool], Function[bool]], bool]) -> Function[bool]:
    return lambda: converter(f1, f2)

def FuncAndAlso(f1: Function[bool], f2: Function[bool]) -> bool:
    return f1() and f2()
def GetAndAlsoFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncAndAlso)

def FuncAnd(f1: Function[bool], f2: Function[bool]) -> bool:
    return f1() & f2()
def GetAndFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncAnd)

def FuncOrElse(f1: Function[bool], f2: Function[bool]) -> bool:
    return f1() or f2()
def GetOrElseFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncOrElse)

def FuncOr(f1: Function[bool], f2: Function[bool]) -> bool:
    return f1() | f2()
def GetOrFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncOr)

def FuncNotAndAlso(f1: Function[bool], f2: Function[bool]) -> bool:
    return (not f1()) and f2()
def GetNotAndAlsoFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncNotAndAlso)

def FuncNotAnd(f1: Function[bool], f2: Function[bool]) -> bool:
    return (not f1()) & f2()
def GetNotAndFunc(f1: Function[bool], f2: Function[bool]) -> Function[bool]:
    return __GetFunction(f1, f2, FuncNotAnd)

def FuncNot(func: Function[bool]) -> bool:
    return not func()
def GetNotFunc(func: Function[bool]) -> Function[bool]:
    return lambda: not func()



def GetEqualityComparison[T](value: T) -> EqualityComparison:
    return lambda _value: value == _value

def GetIndexedValueIndexComparison[T](index: int) -> IndexedValueComparison[T]:
    return lambda i, _: i == index

def GetIndexedValueValueComparison[T](value: T) -> IndexedValueComparison[T]:
    return lambda _, _value: value == _value

def GetIndexedValueComparison[T](index: int, value: T) -> IndexedValueComparison[T]:
    return lambda i, _value: i == index and value == _value