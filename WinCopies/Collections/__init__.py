from __future__ import annotations

from collections.abc import Generator as GeneratorBase
from enum import Flag
from typing import final, Callable, NoReturn

from WinCopies import Abstract
from WinCopies.Typing import INullable, Error, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Predicate

type ReadOnlyArray[T] = tuple[T, ...]
type Generator[T] = GeneratorBase[T, None, None]

class EnumerationOrder(Flag):
    Null = 0
    FIFO = 1
    LIFO = 2
    Both = 3

def GetInvalidEnumerationOrderError(order: EnumerationOrder) -> Exception: return ValueError("Unknown enumeration order.", order)
def ThrowInvalidEnumerationOrderError(order: EnumerationOrder) -> NoReturn: raise GetInvalidEnumerationOrderError(order)

class EmptyException(Error):
    def __init__(self, *args: object) -> None: super().__init__("The collection is empty.", *args)

# A key already held: a KeyError, as the framework names every refusal that bears on a key, and a
# ValueError, as Python names a value it refuses -- Python raises KeyError for an absent key only.
# Either reader finds the type it expects, and the type itself tells "already held" from "absent".
class DuplicateKeyError(Error, KeyError, ValueError):
    def __init__(self, message: str, duplicate: INullable[object] = GetNullValue(), *args: object) -> None:
        super().__init__(message, *args)

        self.__duplicate: INullable[object] = duplicate

    # What is held twice, when the route that refuses knows it -- a nullable, since a set may hold
    # None. A range refused as a whole does not: it is not its part to look for the item at fault.
    @final
    def GetDuplicate(self) -> INullable[object]: return self.__duplicate

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
        if predicate(entry): return True
        
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