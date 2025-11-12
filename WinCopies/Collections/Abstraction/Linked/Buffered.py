from collections.abc import Iterable
from typing import final, Callable

from WinCopies.Collections import IList
from WinCopies.Collections.Abstraction.Collection import List
from WinCopies.Collections.Abstraction.Linked import ListBase

from WinCopies.Typing import GenericConstraint, IGenericConstraintImplementation, INullable

class BufferedList[TItems, TList](ListBase[TItems], GenericConstraint[TList, IList[TItems]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def TryPeek(self) -> INullable[TItems]:
        return self._GetInnerContainer().TryGetValue(0)
    
    @final
    def TryPop(self) -> INullable[TItems]:
        result: INullable[TItems] = self.TryPeek()
        
        if result.HasValue():
            self._GetInnerContainer().TryRemoveAt(0)
        
        return result
    
    @final
    def Clear(self) -> None:
        self._GetInnerContainer().Clear()

class BufferedQueueBase[TItems, TList](BufferedList[TItems, TList]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @final
    def Push(self, value: TItems) -> None:
        self._GetInnerContainer().Add(value)
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        return self._GetInnerContainer().AddItems(items)
class BufferedStackBase[TItems, TList](BufferedList[TItems, TList]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @final
    def Push(self, value: TItems) -> None:
        if self.IsEmpty():
            self._GetInnerContainer().Add(value)
        
        else:
            self._GetInnerContainer().Insert(0, value)
    @final
    def TryPushItems(self, items: Iterable[TItems]|None) -> bool:
        def insert(index: int, item: TItems) -> None:
            self._GetInnerContainer().TryInsert(index, item)
        def add(index: int, item: TItems) -> None:
            nonlocal adder

            if self.IsEmpty():
                self._GetInnerContainer().Add(item)
            
            else:
                insert(index, item)
            
            adder = insertItem
        
        def insertItem(index: int, item: TItems) -> None:
            nonlocal i

            i += 1

            insert(index, item)
        
        if items is None:
            return False
        
        adder: Callable[[int, TItems], None] = add
        i: int = 0

        for item in items:
            adder(i, item)

        return True

@staticmethod
def _GetList[T](l: IList[T]|None) -> IList[T]:
    return List[T]() if l is None else l

class BufferedQueue[T](BufferedQueueBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]|None = None):
        super().__init__(_GetList(l))
class BufferedStack[T](BufferedStackBase[T, IList[T]], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, l: IList[T]|None = None):
        super().__init__(_GetList(l))