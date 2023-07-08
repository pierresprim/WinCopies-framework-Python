from typing import Generic, _T, final

from WinCopies import GetIndex

class CircularList(Generic[_T]):
    def __init__(self, items: list[_T], start: int):
        self.__list: list[_T] = items
        self.__start: int = start % len(items)
    
    @final
    def GetIndex(self, index: int) -> int:
        return GetIndex(index, len(self.__list), self.__start)[0]
    
    @final
    def GetLength(self) -> int:
        return len(self.__list)
    
    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int) -> None:
        self.__start = start
    
    @final
    def Add(self, value) -> None:
        self.__list.append(value)
    
    @final
    def Insert(self, index: int, value: _T) -> None:
        self.__list.insert(self.GetIndex(index), value)
    
    @final
    def Remove(self, value: _T) -> None:
        self.__list.remove(value)
    @final
    def RemoveAt(self, index) -> None:
        self.__list.pop(self.GetIndex(index))
    
    @final
    def Clear(self) -> None:
        self.__list.clear()
    
    @final
    def __getitem__(self, key: int) -> _T:
        if key is int:
            return list[self.GetIndex(key)]
        
        raise TypeError("Invalid key type: 'key' must be 'int'.")