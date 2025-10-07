from typing import Callable
from collections.abc import Iterable

import WinCopies

from WinCopies import Delegates
from WinCopies.Collections import Enumeration
from WinCopies.Typing.Delegate import Action, Method, Function, Predicate
from WinCopies.Typing.Pairing import DualValueBool

def While(func: Function[bool], action: Action) -> bool:
    """Executes the given action while the given condition is True.

    Args:
        func: The condition function to evaluate.
        action: The action to execute on each iteration.

    Returns:
        True if the loop executed at least once, False otherwise.
    """
    if (func := Delegates.GetBoolFuncAction(func, action))():
        while func():
            pass
        
        return True

    return False
def Until(func: Function[bool], action: Action) -> bool:
    """Executes the given action until the given condition is True.

    Args:
        func: The condition function to evaluate.
        action: The action to execute on each iteration.

    Returns:
        True if the loop executed at least once, False if the condition was already True.
    """
    if func():
        return False
    
    action()
    
    while not func():
        action()

    return True

def __Do(action: Action, func: Function[bool], loop: Callable[[Function[bool], Action], bool]) -> bool:
    action()

    return loop(func, action)
def DoWhile(action: Action, func: Function[bool]) -> bool:
    """Executes the given action at least once, then continues while the given condition is True.

    Args:
        action: The action to execute on each iteration.
        func: The condition function to evaluate.

    Returns:
        True if the loop executed at least once, False otherwise.
    """
    return __Do(action, func, While)
def DoUntil(action: Action, func: Function[bool]) -> bool:
    """Executes the given action at least once, then continues until the given condition is True.

    Args:
        action: The action to execute on each iteration.
        func: The condition function to evaluate.

    Returns:
        True if the loop executed at least once, False if the condition was already True after first execution.
    """
    return __Do(action, func, Until)

def ForEachUntilTrue[T](items: Iterable[T], action: Callable[[int, T], bool]) -> DualValueBool[int]|None:
    """Iterates over items with index, executing the given action until it returns True.

    Args:
        items: The items to iterate over.
        action: A function taking index and item, returning True to stop iteration.

    Returns:
        - None if no items
        - DualValueBool with last index and False if stopped early, or DualValueBool with last index and True if completed all items.
    """
    i: int = -1

    for item in items:
        i += 1

        if action(i, item):
            return DualValueBool(i, False)
    
    return None if i == -1 else DualValueBool(i, True)
def ForEachItemUntil[T](items: Iterable[T], predicate: Predicate[T]) -> bool|None:
    """Iterates over items until the given predicate returns True.

    Args:
        items: The items to iterate over.
        predicate: A function to test each item.

    Returns:
        - None if no items processed
        - True if predicate matched
        - False if completed without match.
    """
    enumerator: Enumeration.IEnumerator[T] = Enumeration.Iterable[T].Create(items).GetEnumerator()

    for entry in enumerator.AsIterator():
        if predicate(entry):
            return True
    
    return False if enumerator.HasProcessedItems() else None

def ForEach[T](items: Iterable[T], action: Callable[[int, T], bool]) -> DualValueBool[int]|None:
    """Iterates over items with index, executing the given action while it returns True.

    Args:
        items: The items to iterate over.
        action: A function taking index and item, returning False to stop iteration.

    Returns:
        - None if no items
        - DualValueBool with last index and False if stopped early, or DualValueBool with last index and True if completed all items.
    """
    return ForEachUntilTrue(items, lambda index, item: not action(index, item))
def ForEachValue[T](action: Callable[[int, T], bool], *values: T) -> DualValueBool[int]|None:
    """Iterates over variadic values with index, executing the given action while it returns True.

    Args:
        action: A function taking index and value, returning False to stop iteration.
        *values: The values to iterate over.

    Returns:
        - None if no values
        - DualValueBool with last index and False if stopped early, or DualValueBool with last index and True if completed all values.
    """
    return ForEach(values, action)

def DoForEach[T](items: Iterable[T], action: Callable[[int, T], None]) -> int:
    """Executes the given action for each item with its index.

    Args:
        items: The items to iterate over.
        action: A function taking index and item.

    Returns:
        The last index processed, or -1 if no items.
    """
    i: int = -1

    for item in items:
        i += 1

        action(i, item)
    
    return i
def DoForEachValue[T](action: Callable[[int, T], None], *values: T) -> int:
    """Executes the given action for each variadic value with its index.

    Args:
        action: A function taking index and value.
        *values: The values to iterate over.

    Returns:
        The last index processed, or -1 if no values.
    """
    return DoForEach(values, action)

def ForEachItem[T](items: Iterable[T], predicate: Predicate[T]) -> bool|None:
    """Iterates over items while the given predicate returns True.

    Args:
        items: The items to iterate over.
        predicate: A function to test each item.

    Returns:
        - None if no items processed
        - True if completed all items
        - False if stopped early.
    """
    return WinCopies.Not(ForEachItemUntil(items, Delegates.GetNotPredicate(predicate)))
def ForEachArg[T](predicate: Predicate[T], *values: T) -> bool|None:
    """Iterates over variadic values while the given predicate returns True.

    Args:
        predicate: A function to test each value.
        *values: The values to iterate over.

    Returns:
        - None if no values processed
        - True if completed all values
        - False if stopped early.
    """
    return ForEachItem(values, predicate)

def DoForEachItem[T](items: Iterable[T], action: Method[T]) -> bool:
    """Executes the given action for each item in items.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.

    Returns:
        True if at least one item was processed, False otherwise.
    """
    enumerator: Enumeration.IEnumerator[T] = Enumeration.Iterable[T].Create(items).GetEnumerator()

    for entry in enumerator.AsIterator():
        action(entry)
    
    return enumerator.HasProcessedItems()
def DoForEachArg[T](action: Callable[[T], None], *values: T) -> bool|None:
    """Executes the given action for each variadic value.

    Args:
        action: A function to execute for each value.
        *values: The values to iterate over.

    Returns:
        True if at least one value was processed, False otherwise.
    """
    return DoForEachItem(values, action)

def ForEachWhile[T](items: Iterable[T], predicate: Callable[[int, T], bool], action: Callable[[int, T], None]) -> DualValueBool[int]|None:
    """Executes the given action for items while the given predicate is False.

    Args:
        items: The items to iterate over.
        predicate: A function to test each item with its index; iteration stops when True.
        action: A function to execute for each item before the predicate returns True.

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    def _action(i: int, value: T) -> bool:
        if (predicate(i, value)):
            return False

        action(i, value)
        
        return True

    return ForEachUntilTrue(items, _action)

def ForEachWhileIndex[T](items: Iterable[T], action: Callable[[int, T], None], index: int) -> DualValueBool[int]|None:
    """Executes the given action for items until reaching a specific index.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        index: The index at which to stop.

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachWhile(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachWhileValue[T](items: Iterable[T], action: Callable[[int, T], None], value: T) -> DualValueBool[int]|None:
    """Executes the given action for items until finding a specific value.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        value: The value at which to stop.

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachWhile(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachWhileIndexAndValue[T](items: Iterable[T], action: Callable[[int, T], None], index: int, value: T) -> DualValueBool[int]|None:
    """Executes the given action for items until reaching a specific index and value.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        index: The index at which to check.
        value: The value at which to stop.

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachWhile(items, Delegates.GetIndexedValueComparison(index, value), action)

def ForEachUntil[T](items: Iterable[T], predicate: Callable[[int, T], bool], action: Callable[[int, T], None]) -> DualValueBool[int]|None:
    """Executes the given action for items until the given predicate is True.

    Args:
        items: The items to iterate over.
        predicate: A function to test each item with its index; iteration stops when True.
        action: A function to execute for each item including when the predicate returns True.

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    def _action(i: int, value: T) -> bool:
        if (predicate(i, value)):
            action(i, value)

            return True
        
        return False

    return ForEachUntilTrue(items, _action)

def ForEachUntilIndex[T](items: Iterable[T], action: Callable[[int, T], None], index: int) -> DualValueBool[int]|None:
    """Executes the given action for items until reaching a specific index.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        index: The index at which to stop (inclusive).

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachUntil(items, Delegates.GetIndexedValueIndexComparison(index), action)
def ForEachUntilValue[T](items: Iterable[T], action: Callable[[int, T], None], value: T) -> DualValueBool[int]|None:
    """Executes the given action for items until finding a specific value.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        value: The value at which to stop (inclusive).

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachUntil(items, Delegates.GetIndexedValueValueComparison(value), action)
def ForEachUntilIndexAndValue[T](items: Iterable[T], action: Callable[[int, T], None], index: int, value: T) -> DualValueBool[int]|None:
    """Executes the given action for items until reaching a specific index and value.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item.
        index: The index at which to check.
        value: The value at which to stop (inclusive).

    Returns:
        None if no items, DualValueBool with last index and status otherwise.
    """
    return ForEachUntil(items, Delegates.GetIndexedValueComparison(index, value), action)

def ScanItems[T](items: Iterable[T], predicate: Predicate[T], action: Method[T]) -> bool|None:
    """Scans items and executes the given action only while all items match a predicate.

    Args:
        items: The items to scan.
        predicate: A function to test each item.
        action: A function to execute for matching items.

    Returns:
        None if no items, True if all items matched, False if at least one did not match.
    """
    result: bool|None = None
    
    def scan(entry: T):
        if predicate(entry):
            action(entry)
    
    def tryScan(entry: T):
        nonlocal func
        nonlocal result

        if predicate(entry):
            action(entry)
        
        else:
            func = scan

            result = False

    func: Method[T]

    def init(entry: T):
        nonlocal result
        nonlocal func

        result = True

        (func := tryScan)(entry)
    
    func = init

    for entry in items:
        func(entry)
    
    return result

def __ForEachButFirst[T](items: Iterable[T], action: Predicate[T], func: Callable[[Iterable[T], Predicate[T]], bool|None], returnValue: bool) -> bool|None:
    _action: Predicate[T]
    
    def __action(_: T) -> bool:
        nonlocal _action

        _action = action

        return returnValue
    
    _action = __action
    
    return func(items, lambda item: _action(item))
def ForEachButFirst[T](items: Iterable[T], action: Predicate[T]) -> bool|None:
    """Executes the given action for all items except the first, while the action returns True.

    Args:
        items: The items to iterate over.
        action: A predicate to execute for each item except the first.

    Returns:
        None if no items processed, True if completed all items, False if stopped early.
    """
    return __ForEachButFirst(items, action, ForEachItem, True)
def ForEachUntilButFirst[T](items: Iterable[T], action: Predicate[T]) -> bool|None:
    """Executes the given action for all items except the first, until the action returns True.

    Args:
        items: The items to iterate over.
        action: A predicate to execute for each item except the first.

    Returns:
        None if no items processed, True if action matched, False if completed without match.
    """
    return __ForEachButFirst(items, action, ForEachItemUntil, False)

def __ForEachAndFirst[T](items: Iterable[T], firstAction: Predicate[T], action: Predicate[T], func: Callable[[Iterable[T], Predicate[T]], bool|None], returnValue: bool) -> bool|None:
    _action: Predicate[T]
    
    def __action(item: T) -> bool:
        nonlocal _action

        if firstAction(item):
            _action = action

            return returnValue
        
        else:
            return not returnValue
    
    _action = __action

    return func(items, lambda item: _action(item))
def ForEachAndFirst[T](items: Iterable[T], firstAction: Predicate[T], action: Predicate[T]) -> bool|None:
    """Executes a special action for the first item, then a different one for the rest.

    Args:
        items: The items to iterate over.
        firstAction: A predicate to execute for the first item.
        action: A predicate to execute for subsequent items.

    Returns:
        None if no items processed, True if completed all items, False if stopped early.
    """
    return __ForEachAndFirst(items, firstAction, action, ForEachItem, True)
def ForEachUntilAndFirst[T](items: Iterable[T], firstAction: Predicate[T], action: Predicate[T]) -> bool|None:
    """Executes a special action for the first item, then a different one until it returns True.

    Args:
        items: The items to iterate over.
        firstAction: A predicate to execute for the first item.
        action: A predicate to execute for subsequent items.

    Returns:
        None if no items processed, True if action matched, False if completed without match or first action failed.
    """
    return __ForEachAndFirst(items, firstAction, action, ForEachItemUntil, False)

def DoForEachButFirst[T](items: Iterable[T], action: Method[T]) -> bool:
    """Executes the given action for all items except the first.

    Args:
        items: The items to iterate over.
        action: A function to execute for each item except the first.

    Returns:
        True if at least one item was processed, False otherwise.
    """
    _action: Method[T]
    
    def __action(_: T):
        nonlocal _action

        _action = action
    
    _action = __action
    
    return DoForEachItem(items, lambda item: _action(item))
def DoForEachAndFirst[T](items: Iterable[T], firstAction: Method[T], action: Method[T]) -> bool:
    """Executes a special action for the first item, then a different one for the rest.

    Args:
        items: The items to iterate over.
        firstAction: A function to execute for the first item.
        action: A function to execute for subsequent items.

    Returns:
        True if at least one item was processed, False otherwise.
    """
    _action: Method[T]
    
    def __action(item: T):
        nonlocal _action

        firstAction(item)

        _action = action
    
    _action = __action

    return DoForEachItem(items, lambda item: _action(item))