from typing import Callable
from collections.abc import Iterable

import WinCopies
from WinCopies import Delegates
from WinCopies.Typing.Pairing import DualValueBool

def While(func: Callable[[], bool], action: Callable[[], None]) -> bool:
    if (func := Delegates.GetBoolFuncAction(func, action))():
        while func():
            pass
        
        return True

    return False
def Until(func: Callable[[], bool], action: Callable[[], None]) -> bool:
    if func():
        return False
    
    action()
    
    while not func():
        action()

    return True

def __Do(action: Callable[[], None], func: Callable[[], bool], loop: Callable[[Callable[[], bool], Callable[[], None]], bool]) -> bool:
    action()

    return loop(func, action)
def DoWhile(action: Callable[[], None], func: Callable[[], bool]) -> bool:
    return __Do(action, func, While)
def DoUntil(action: Callable[[], None], func: Callable[[], bool]) -> bool:
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

def DoForEach[T](items: Iterable[T], action: Callable[[int, T], None]) -> int:
    i: int = -1

    for item in items:
        i += 1

        action(i, item)
    
    return i
def DoForEachValue[T](action: Callable[[int, T], None], *values: T) -> int:
    return DoForEach(values, action)

def ForEachItem[T](items: Iterable[T], predicate: Callable[[T], bool]) -> bool|None:
    return WinCopies.Not(ForEachItemUntil(items, Delegates.GetNotPredicate(predicate)))
def ForEachArg[T](predicate: Callable[[T], bool], *values: T) -> bool|None:
    return ForEachItem(values, predicate)

def DoForEachItem[T](items: Iterable[T], action: Callable[[T], None]) -> bool:
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
def DoForEachArg[T](action: Callable[[T], None], *values: T) -> bool|None:
    return DoForEachItem(values, action)

def ForEachWhile[T](items: Iterable[T], predicate: Callable[[int, T], bool], action: Callable[[int, T], None]) -> DualValueBool[int]|None:
    def _action(i: int, value: T) -> bool:
        nonlocal predicate
        nonlocal action

        if (predicate(i, value)):
            return False

        action(i, value)
        
        return True

    return ForEachUntilTrue(items, _action)

def ForEachWhileIndex[T](items: Iterable[T], action: Callable[[int, T], None], index: int) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachWhileValue[T](items: Iterable[T], action: Callable[[int, T], None], value: T) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachWhileIndexAndValue[T](items: Iterable[T], action: Callable[[int, T], None], index: int, value: T) -> DualValueBool[int]|None:
    return ForEachWhile(items, Delegates.GetIndexedValueComparison(index, value), action)

def ForEachUntil[T](items: Iterable[T], predicate: Callable[[int, T], bool], action: Callable[[int, T], None]) -> DualValueBool[int]|None:
    def _action(i: int, value) -> bool:
        if (predicate(i, value)):
            action(i, value)

            return True
        
        return False

    return ForEachUntilTrue(items, _action)

def ForEachUntilIndex[T](items: Iterable[T], action: Callable[[int, T], None], index: int) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachUntilValue[T](items: Iterable[T], action: Callable[[int, T], None], value: T) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachUntilIndexAndValue[T](items: Iterable[T], action: Callable[[int, T], None], index: int, value: T) -> DualValueBool[int]|None:
    return ForEachUntil(items, Delegates.GetIndexedValueComparison(index, value), action)

def ScanItems[T](items: Iterable[T], predicate: Callable[[T], bool], action: Callable[[T], None]) -> bool|None:
    result: bool|None = None
    
    def scan(entry: T):
        nonlocal predicate
        nonlocal action

        if predicate(entry):
            action(entry)
    
    def tryScan(entry: T):
        nonlocal predicate
        nonlocal action
        nonlocal func
        nonlocal result

        if predicate(entry):
            action(entry)
        
        else:
            func = scan

            result = False

    func: Callable[[T]]

    def init(entry: T):
        nonlocal result
        nonlocal func

        result = True

        (func := tryScan)(entry)
    
    func = init

    for entry in items:
        func(entry)
    
    return result

def __ForEachButFirst[T](items: Iterable[T], action: Callable[[T], bool], func: Callable[[Iterable[T], Callable[[T], bool]], bool|None], returnValue: bool) -> bool|None:
    _action: Callable[[T], bool]
    
    def __action(item: T) -> bool:
        nonlocal action
        nonlocal _action
        nonlocal returnValue

        _action = action

        return returnValue
    
    _action = __action
    
    return func(items, lambda item: _action(item))
def ForEachButFirst[T](items: Iterable[T], action: Callable[[T], bool]) -> bool|None:
    return __ForEachButFirst(items, action, ForEachItem, True)
def ForEachUntilButFirst[T](items: Iterable[T], action: Callable[[T], bool]) -> bool|None:
    return __ForEachButFirst(items, action, ForEachItemUntil, False)

def __ForEachAndFirst[T](items: Iterable[T], firstAction: Callable[[T], bool], action: Callable[[T], bool], func: Callable[[Iterable[T], Callable[[T], bool]], bool|None], returnValue: bool) -> bool|None:
    _action: Callable[[T], bool]
    
    def __action(item: T) -> bool:
        nonlocal firstAction
        nonlocal action
        nonlocal _action
        nonlocal returnValue

        if firstAction(item):
            _action = action

            return returnValue
        
        else:
            return not returnValue
    
    _action = __action

    return func(items, lambda item: _action(item))
def ForEachAndFirst[T](items: Iterable[T], firstAction: Callable[[T], bool], action: Callable[[T], bool]) -> bool|None:
    return __ForEachAndFirst(items, firstAction, action, ForEachItem, True)
def ForEachUntilAndFirst[T](items: Iterable[T], firstAction: Callable[[T], bool], action: Callable[[T], bool]) -> bool|None:
    return __ForEachAndFirst(items, firstAction, action, ForEachItemUntil, False)

def DoForEachButFirst[T](items: Iterable[T], action: Callable[[T], None]) -> bool:
    _action: Callable[[T]]
    
    def __action(item: T):
        nonlocal action
        nonlocal _action

        _action = action
    
    _action = __action
    
    return DoForEachItem(items, lambda item: _action(item))
def DoForEachAndFirst[T](items: Iterable[T], firstAction: Callable[[T], None], action: Callable[[T], None]) -> bool:
    _action: Callable[[T]]
    
    def __action(item: T):
        nonlocal firstAction
        nonlocal action
        nonlocal _action

        firstAction(item)
        _action = action
    
    _action = __action

    return DoForEachItem(items, lambda item: _action(item))