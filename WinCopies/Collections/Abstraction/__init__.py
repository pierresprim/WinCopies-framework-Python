import collections.abc
import typing

from typing import final

from WinCopies.Collections import Extensions, IndexOf
from WinCopies.Typing.Delegate import Predicate

class Array[T](Extensions.Array[T]):
    def __init__(self, items: tuple[T, ...]|collections.abc.Iterable[T]):
        super().__init__()

        self.__tuple: tuple[T] = items if isinstance(items, tuple) else tuple(items)
    
    def _GetTuple(self) -> tuple[T]:
        return self.__tuple
    
    @final
    def GetCount(self) -> int:
        return len(self._GetTuple())
    
    @final
    def GetAt(self, index: int) -> T:
        return self._GetTuple()[index]

class List[T](Extensions.List[T]):
    def __init__(self, items: list[T]|None = None):
        super().__init__()

        self.__list: list[T] = list[T]() if items is None else items
    
    @final
    def _GetList(self) -> list[T]:
        return self.__list
    
    @final
    def GetCount(self) -> int:
        return len(self._GetList())
    
    @final
    def GetAt(self, index: int) -> T:
        return self._GetList()[index]
    @final
    def SetAt(self, index: int, value: T) -> None:
        self._GetList()[index] = value
    
    @final
    def Add(self, item: T) -> None:
        self._GetList().append(item)
    
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetList().pop(index)
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0:
            return None
        
        if index >= self.GetCount():
            return False
        
        self.RemoveAt(index)
        
        return True
    
    @final
    def TryRemove(self, item: T, predicate: Predicate[T]|None = None) -> bool:
        items: list[T] = self._GetList()

        index: int|None = IndexOf(items, item, predicate)

        if index is None:
            return False
        
        items.pop(index)

        return True
    @final
    def Remove(self, item: T, predicate: Predicate[T]|None = None) -> None:
        if not self.TryRemove(item, predicate):
            raise ValueError(item)
    
    @final
    def Clear(self) -> None:
        self._GetList().clear()