from typing import final

from WinCopies import Collections

class CircularList[T]:
    def __init__(self, items: list[T], start: int = 0):
        self.__list: list[T] = items
        self.__start: int = start % len(items)
    
    @final
    def _GetList() -> list[T]:
        return self.__list
    
    @final
    def GetIndex(self, index: int) -> int:
        return Collections.GetIndex(index, self.GetLength(), self.GetStart())[0]
    
    @final
    def GetLength(self) -> int:
        return len(self._GetList())
    
    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int = 0) -> None:
        self.__start = start
    
    @final
    def Add(self, value: T) -> None:
        self._GetList().append(value)
    
    @final
    def Insert(self, index: int, value: T) -> None:
        self._GetList().insert(self.GetIndex(index), value)
    
    @final
    def Remove(self, value: T) -> None:
        self._GetList().remove(value)
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetList().pop(self.GetIndex(index))
    
    @final
    def Clear(self) -> None:
        self._GetList().clear()
    
    @final
    def __getitem__(self, index: int) -> T:
        return self._GetList()[self.GetIndex(index)]