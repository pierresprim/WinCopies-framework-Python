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
def Until(action: callable, func: callable) -> bool:
    if func():
        return False
    
    while True:
        action()

        if func():
            return True
def DoWhile(action: callable, func: callable) -> bool:
    action()

    if func():
        action()

        while func():
            action()
        
        return True
    
    return False
def DoUntil(action: callable, func: callable) -> bool:
    action()

    return Until(action, func)

def ForEach(list, action: callable) -> bool:
    for i in range(len(list)):
        if action(i, list[i]):
            continue

        return False
    
    return True

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