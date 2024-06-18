from abc import ABC, abstractmethod
from typing import final

from WinCopies import DualValueBool
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
    return ForEachWhile(list, action, GetIndexedValueIndexComparison(value))

def ForEachWhileValue(list, action: callable, value) -> bool:
    return ForEachWhile(list, action, GetIndexedValueValueComparison(value))

def ForEachWhileIndexAndValue(list, action: callable, value) -> bool:
    return ForEachWhile(list, action, GetIndexedValueComparison(value))

def ForEachUntil(list, action: callable, predicate: callable) -> bool:
    def _action(i: int, value) -> bool:
        if (predicate(i, value)):
            action(i, value)

            return False
        
        return True

    return ForEach(list, _action)

def ForEachUntilIndex(list, action: callable, value) -> bool:
    return ForEachUntil(list, action, GetIndexedValueIndexComparison(value))

def ForEachUntilValue(list, action: callable, value) -> bool:
    return ForEachUntil(list, action, GetIndexedValueValueComparison(value))

def ForEachUntilIndexAndValue(list, action: callable, value) -> bool:
    return ForEachUntil(list, action, GetIndexedValueComparison(value))

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

class EmptyException(Exception):
    def __init__(self):
        pass

class Collection(ABC):
    def __init__(self):
        pass
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        pass
    
    def HasItems(self) -> bool:
        return not self.Empty()
    
    def ThrowIfEmpty(self) -> None:
        if self.Empty():
            raise EmptyException()

class FinderPredicate[T]:
    def __init__(self):
        self.__Reset()
    
    def __Reset(self):
        self.__result: T|None = None
        self.__hasValue: bool = False
    
    def __Set(self, result: T):
        self.__result = result
        self.__hasValue = True

    def __Scan(self, entry: T, predicate: callable) -> bool:
        if predicate(entry):
            self.__Set(entry)

            return True
        
        return False

    def __Validate(self, entry: T, predicate: callable) -> bool:
        if predicate(entry):
            return True
        
        self.__Set(entry)
        
        return False
    
    def __GetPredicate(self, predicate: callable, func: callable) -> callable:
        self.__Reset()

        return lambda entry: func(entry, predicate)
    
    def GetPredicate(self, predicate: callable) -> callable:
        return self.__GetPredicate(predicate, self.__Scan)
    
    def GetValidationPredicate(self, predicate: callable) -> callable:
        return self.__GetPredicate(predicate, self.__Validate)
    
    def TryGetResult(self) -> DualValueBool[T]:
        return DualValueBool(self.__result, self.__hasValue)
    
    def GetResult(self) -> T:
        if self.__hasValue:
            return self.__result
        
        raise ValueError('This object contains no value.')