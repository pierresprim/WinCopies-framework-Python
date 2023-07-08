from abc import ABC, abstractmethod
from typing import Generic, _T

from WinCopies.Delegates import GetIndexedValueComparison, GetIndexedValueIndexComparison, GetIndexedValueValueComparison

def GetLastIndex(list) -> int:
    return len(list) - 1

def TrySetAt(list, index: int, ifTrue: callable, ifFalse: callable):
    return ifTrue(index) if len(list) > index else ifFalse()

def TryGetAt(list, index: int, default):
    return list[index] if len(list) > index else default
def TryGetAtNone(list, index: int):
    return list[index] if len(list) > index else None
def TryGetAtFunc(list, index: int, ifTrue: callable, ifFalse: callable):
    return TrySetAt(list, index, lambda i: ifTrue(list[i]), ifFalse)
def TryGetAtStr(list, index: int):
    return TryGetAt(list, index, "")

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

def ForEachWhileIndex(list, action: callable, value) -> bool:
    ForEachWhile(list, action, GetIndexedValueIndexComparison(value))

def ForEachWhileValue(list, action: callable, value) -> bool:
    ForEachWhile(list, action, GetIndexedValueValueComparison(value))

def ForEachWhileIndexAndValue(list, action: callable, value) -> bool:
    ForEachWhile(list, action, GetIndexedValueComparison(value))

def ForEachUntil(list, action: callable, predicate: callable) -> bool:
    def _action(i: int, value) -> bool:
        if (predicate(i, value)):
            action(i, value)

            return False
        
        return True

    return ForEach(list, _action)

def ForEachUntilIndex(list, action: callable, value) -> bool:
    ForEachUntil(list, action, GetIndexedValueIndexComparison(value))

def ForEachUntilValue(list, action: callable, value) -> bool:
    ForEachUntil(list, action, GetIndexedValueValueComparison(value))

def ForEachUntilIndexAndValue(list, action: callable, value) -> bool:
    ForEachUntil(list, action, GetIndexedValueComparison(value))

class EmptyException(Exception):
    def __init__(self):
        pass

class Collection(ABC, Generic[_T]):
    def __init__(self):
        pass
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        pass
    
    def HasItems(self) -> bool:
        return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty():
            raise EmptyException()