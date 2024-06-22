from typing import Callable
from collections.abc import Iterable

import WinCopies
from WinCopies import DualValueBool, Delegates

def While(func: Callable[[], bool], action: Callable[[]]) -> bool:
    if (func := Delegates.GetBoolFuncAction(func, action))():
        while func():
            pass
        
        return True

    return False
def Until(func: Callable[[], bool], action: Callable[[]]) -> bool:
    if func():
        return False
    
    action()
    
    while not func():
        action()

    return True

def __Do(action: Callable[[]], func: Callable[[], bool], loop: Callable[[Callable[[], bool], Callable[[]]]]) -> bool:
    action()

    return loop(func, action)
def DoWhile(action: Callable[[]], func: Callable[[], bool]) -> bool:
    return __Do(action, func, While)
def DoUntil(action: Callable[[]], func: Callable[[], bool]) -> bool:
    return __Do(action, func, Until)

def ForEachUntilTrue[T](items: Iterable[T], action: Callable[[int, T], bool]) -> DualValueBool[int]|None:
    i: int = -1

    for item in items:
        i += 1

        if action(i, item):
            return DualValueBool(i, False)
    
    return None if i == -1 else DualValueBool(i, True)
def ForEachItemUntil[T](items: Iterable[T], predicate: Callable[[T], bool]) -> bool|None:
    result: bool|None = None
    _predicate: Callable[[T], bool]

    def init(entry: T) -> bool:
        nonlocal result
        nonlocal predicate
        nonlocal _predicate

        result = False
        return (_predicate := predicate)(entry)
    
    _predicate = init

    for entry in items:
        if _predicate(entry):
            return True
    
    return result

def ForEach[T](items: Iterable[T], action: Callable[[int, T], bool]) -> DualValueBool[int]|None:
    return ForEachUntilTrue(items, lambda index, _action: not action(index, action))
def ForEachValue[T](action: Callable[[int, T], bool], *values: T) -> DualValueBool[int]|None:
    return ForEach(values, action)

def DoForEach[T](items: Iterable[T], action: Callable[[int, T]]) -> int:
    i: int = -1

    for item in items:
        i += 1

        action(i, item)
    
    return i
def DoForEachValue[T](action: Callable[[int, T]], *values: T) -> int:
    return DoForEach(values, action)

def ForEachItem[T](items: Iterable[T], predicate: Callable[[T], bool]) -> bool|None:
    return WinCopies.Not(ForEachItemUntil(items, Delegates.GetNotPredicate(predicate)))
def ForEachArg[T](predicate: Callable[[T], bool], *values: T) -> bool|None:
    return ForEachItem(values, predicate)

def DoForEachItem[T](items: Iterable[T], action: Callable[[T]]) -> bool:
    result: bool = False
    _action: Callable[[T]]

    def init(entry: T):
        nonlocal result
        nonlocal action
        nonlocal _action

        (_action := action)(entry)

        result = True
    
    _action = init

    for entry in items:
        _action(entry)
    
    return result
def DoForEachArg[T](action: Callable[[T]], *values: T) -> bool|None:
    return DoForEachItem(values, predicate)

def ForEachWhile(list, action: callable, predicate: callable) -> bool:
    def _action(i: int, value) -> bool:
        if (predicate(i, value)):
            return True

        action(i, value)
        
        return False

    return ForEach(list, _action)

def ForEachWhileIndex[T](items: Iterable[T], action: Callable[[int, T]], index: int) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachWhileValue[T](items: Iterable[T], action: Callable[[int, T]], value: T) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachWhileIndexAndValue[T](items: Iterable[T], action: Callable[[int, T]], index: int, value: T) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueComparison(index, value), action)

def ForEachUntil(list, action: callable, predicate: callable) -> bool:
    def _action(i: int, value) -> bool:
        if (predicate(i, value)):
            action(i, value)

            return False
        
        return True

    return ForEach(list, _action)

def ForEachUntilIndex[T](items: Iterable[T], action: Callable[[int, T]], index: int) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachUntilValue[T](items: Iterable[T], action: Callable[[int, T]], value: T) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachUntilIndexAndValue[T](items: Iterable[T], action: Callable[[int, T]], index: int, value: T) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueComparison(index, value), action)

def ParseItems(iterable, predicate: callable) -> bool|None:
    result: bool|None = None
    _predicate: callable

    def init(entry) -> bool:
        nonlocal result
        nonlocal predicate
        nonlocal _predicate

        result = False
        return (_predicate := predicate)(entry)
    
    _predicate = init

    for entry in iterable:
        if _predicate(entry):
            return True
    
    return result

def ScanItems(iterable, action: callable) -> bool:
    result: bool = False
    _action: callable

    def init(entry):
        nonlocal result
        nonlocal action
        nonlocal _action

        (_action := action)(entry)

        result = True
    
    _action = init

    for entry in iterable:
        _action(entry)
    
    return result

def ScanAllItems(iterable, predicate: callable, action: callable) -> bool|None:
    result: bool|None = None
    
    def scanDir(entry):
        nonlocal predicate
        nonlocal action

        if predicate(entry):
            action(entry)
    
    def tryScanDir(entry):
        nonlocal predicate
        nonlocal action
        nonlocal func
        nonlocal result

        if predicate(entry):
            action(entry)
        
        else:
            func = scanDir

            result = False

    func: callable

    def init(entry):
        nonlocal result
        nonlocal func

        result = True

        (func := tryScanDir)(entry)
    
    func = init

    for entry in iterable:
        func(entry)
    
    return result