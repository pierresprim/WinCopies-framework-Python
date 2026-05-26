from __future__ import annotations

from collections.abc import Generator as GeneratorBase
from enum import Flag
from typing import Callable

from WinCopies import Abstract, BooleanableEnum, NullableBoolean
from WinCopies.Enum import OrderedEnum
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Predicate

type Generator[T] = GeneratorBase[T, None, None]

class Mutability(OrderedEnum):
    ReadOnly = 0
    FixedSize = 1
    Mutable = 2

class EnumerationOrder(Flag):
    Null = 0
    FIFO = 1
    LIFO = 2
    Both = 3

class IterableScanResult(BooleanableEnum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1
    
    def Not(self) -> IterableScanResult:
        return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self
class IterationResult(BooleanableEnum):
    Error = -1
    Success = 0
    Empty = 1
    Null = 2
    
    def ToNullableBool(self) -> bool|None:
        return True if self == IterationResult.Success else (None if self.value > 0 else False)
    
    def ToNullableBoolean(self) -> NullableBoolean:
        return NullableBoolean.BoolTrue if self == IterationResult.Success else (NullableBoolean.Null if self.value > 0 else NullableBoolean.BoolFalse)

class EmptyException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class FinderPredicate[T](Abstract):
    def __init__(self) -> None:
        super().__init__()
        
        self.__Reset()
    
    def __Reset(self) -> None:
        self.__result: INullable[T] = GetNullValue()
    
    def __Set(self, result: T) -> None:
        self.__result = GetNullable(result)

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
    
    def __GetPredicate(self, predicate: Predicate[T], func: Callable[[T, Predicate[T]], bool]) -> Predicate[T]:
        self.__Reset()

        return lambda entry: func(entry, predicate)
    
    def GetPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Scan)
    
    def GetValidationPredicate(self, predicate: Predicate[T]) -> Predicate[T]:
        return self.__GetPredicate(predicate, self.__Validate)
    
    def GetResult(self) -> INullable[T]:
        return self.__result