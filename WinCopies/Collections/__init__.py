from typing import Callable
from abc import ABC, abstractmethod
from collections.abc import Iterable

from WinCopies import DualValueBool

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

def MakeIterable[T](*items: T) -> Iterable[T]:
    return items

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