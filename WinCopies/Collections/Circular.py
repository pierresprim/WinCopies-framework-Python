from typing import final

from WinCopies import Collections
from WinCopies.Collections import IndexOf
from WinCopies.Collections.Extensions import List
from WinCopies.Typing.Delegate import Predicate

class CircularList[T](List[T]):
    def __init__(self, items: list[T], start: int):
        super().__init__()
        
        self.__list: list[T] = items
        self.__start: int = start % len(items)
    
    @final
    def _GetList(self) -> list[T]:
        return self.__list
    
    @final
    def IsEmpty(self) -> bool:
        return len(self._GetList()) == 0
    
    @final
    def GetIndex(self, index: int) -> int:
        return Collections.GetIndex(index, self.GetCount(), self.GetStart())[0]
    
    @final
    def GetCount(self) -> int:
        return len(self._GetList())
    
    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int = 0) -> None:
        self.__start = start
    
    @final
    def GetAt(self, index: int) -> T:
        return self._GetList()[self.GetIndex(index)]
    @final
    def SetAt(self, index: int, value: T) -> None:
        self._GetList()[self.GetIndex(index)] = value
    
    @final
    def Add(self, value: T) -> None:
        self._GetList().append(value)
    
    @final
    def Insert(self, index: int, value: T) -> None:
        self._GetList().insert(self.GetIndex(index), value)
    
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetList().pop(self.GetIndex(index))
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
    
    def __str__(self) -> str:
        return str(self._GetList())