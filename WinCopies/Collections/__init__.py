import collections.abc

from abc import ABC, abstractmethod
from collections.abc import Iterable
from enum import Enum
from typing import Callable

from WinCopies.Typing.Delegate import Predicate
from WinCopies.Typing.Pairing import DualResult, DualValueBool

type Generator[T] = collections.abc.Generator[T, None, None]

class IterableScanResult(Enum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1

    def __bool__(self):
        return self >= 0
    
    def Not(self):
        return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self

def GetLastIndex(list: list) -> int:
    return len(list) - 1

def TrySetAt[T](list: list, index: int, ifTrue: Callable[[int], T], ifFalse: Callable[[], T]) -> T:
    return ifTrue(index) if len(list) > index else ifFalse()

def TryGetAt[T](list: list[T], index: int, default: T|None = None) -> T|None:
    return list[index] if len(list) > index else default
def TryGetAtFunc[TIn, TOut](list: list[TIn], index: int, ifTrue: Callable[[TIn], TOut], ifFalse: Callable[[], TOut]) -> TOut:
    return TrySetAt(list, index, lambda i: ifTrue(list[i]), ifFalse)
def TryGetAtStr(list: list[str], index: int) -> str:
    return TryGetAt(list, index, "")

def MakeIterable[T](*items: T) -> Iterable[T]:
    return items

def IterateWith[T](itemsProvider: Callable[[], Iterable[T]], func: Callable[[Iterable[T]], bool|None]) -> bool|None:
    with itemsProvider() as items:
        return func(items)
def IterateFrom[TIn, TOut](value: TIn, itemsProvider: Callable[[TIn], Iterable[TOut]], func: Callable[[Iterable[TOut]], bool|None]) -> bool|None:
    return IterateWith(lambda: itemsProvider(value), func)

def TryIterateWith[T](checker: Callable[[], bool], itemsProvider: Callable[[], Iterable[T]], func: Callable[[Iterable[T]], bool|None]) -> IterableScanResult:
    if checker():
        result: bool|None = IterateWith(itemsProvider, func)

        return IterableScanResult.Empty if result == None else (IterableScanResult.Success if result else IterableScanResult.Error)
    
    return IterableScanResult.DoesNotExist
def TryIterateFrom[TIn, TOut](value: TIn, checker: Callable[[TIn], bool], itemsProvider: Callable[[TIn], Iterable[TOut]], func: Callable[[Iterable[TOut]], bool|None]) -> IterableScanResult:
    return TryIterateWith(lambda: checker(value), lambda: itemsProvider(value), func)

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
        return not self.IsEmpty()
    
    def ThrowIfEmpty(self) -> None:
        if self.IsEmpty():
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

    def __Scan(self, entry: T, predicate: Predicate[T]) -> bool:
        if predicate(entry):
            self.__Set(entry)
            
            return True
        
        return False

    def __Validate(self, entry: T, predicate: Predicate[T]) -> bool:
        if predicate(entry):
            return True
        
        self.__Set(entry)
        
        return False
    
    def __GetPredicate(self, predicate: Predicate[T], func: callable) -> Predicate[T]:
        self.__Reset()

        return lambda entry: func(entry, predicate)
    
    def GetPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Scan)
    
    def GetValidationPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Validate)
    
    def TryGetResult(self) -> DualValueBool[T]:
        return DualResult[T, bool](self.__result, self.__hasValue)
    
    def GetResult(self) -> T:
        if self.__hasValue:
            return self.__result
        
        raise ValueError('This object contains no value.')