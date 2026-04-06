from typing import final

from WinCopies.Collections import Extensions
from WinCopies.Collections.Enumeration import IEnumerator, TryAsEnumerator
from WinCopies.Collections.Extensions import ISet
from WinCopies.Typing import IEquatableItem

class Set[T: IEquatableItem](Extensions.Set[T]):
    def __init__(self, items: set[T]|None = None) -> None:
        super().__init__()

        self.__set: set[T] = set[T]() if items is None else items
    
    @final
    def __TryAdd(self, item: T) -> int:
        count = self.GetCount()
        
        self._GetItems().add(item)
    
        return count
    
    @final
    def _GetItems(self) -> set[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int:
        return len(self._GetItems())
    
    @final
    def TryAdd(self, item: T) -> bool:
        return self.__TryAdd(item) < self.GetCount()
    @final
    def Add(self, item: T) -> None:
        if self.__TryAdd(item) == self.GetCount():
            raise ValueError(f"Item {item} already exists.")
    
    @final
    def Remove(self, item: T) -> None:
        self._GetItems().remove(item)
    @final
    def TryRemove(self, item: T) -> bool:
        try:
            self.Remove(item)

            return True
        
        except KeyError:
            return False
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(item for item in self._GetItems())
    
    @final
    def Clear(self) -> None:
        self._GetItems().clear()
    
    def ToString(self) -> str:
        return str(self._GetItems())

def CreateSet[T: IEquatableItem](set: set[T]) -> ISet[T]:
    return Set[T](set)