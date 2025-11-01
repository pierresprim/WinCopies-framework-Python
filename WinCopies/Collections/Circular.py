from abc import abstractmethod
from typing import final

from WinCopies import Collections, IStringable
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArray, IList, Tuple, EquatableTuple, Array, List
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, IEquatableItem

class ICircularTuple[T](ITuple[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def IsEmpty(self) -> bool:
        return self.GetCount() == 0
    
    @abstractmethod
    def GetStart(self) -> int:
        pass
    
    @final
    def GetIndex(self, index: int) -> int:
        return Collections.GetIndex(index, self.GetCount(), self.GetStart())[0]
class ICircularEquatableTuple[T: IEquatableItem](ICircularTuple[T], IEquatableTuple[T]):
    def __init__(self):
        super().__init__()
class ICircularArray[T](ICircularTuple[T], IArray[T]):
    def __init__(self):
        super().__init__()
class ICircularList[T](ICircularArray[T], IList[T]):
    def __init__(self):
        super().__init__()

class CircularBase[TItem, TList](GenericConstraint[TList, ITuple[TItem]], ICircularTuple[TItem], IStringable):
    def __init__(self, items: TList, start: int):
        super().__init__()
        
        self.__list: TList = items
        self.__start: int = start % self.GetCount()
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(self.GetIndex(key))
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int = 0) -> None:
        self.__start = start
    
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()

class CircularTuple[T](CircularBase[T, ITuple[T]], Tuple[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], start: int):
        super().__init__(items, start)
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, IEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], start: int):
        super().__init__(items, start)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], GenericSpecializedConstraint[TList, ITuple[TItem], IArray[TItem]], Array[TItem], ICircularArray[TItem]):
    def __init__(self, items: TList, start: int):
        super().__init__(items, start)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(self.GetIndex(key), value)
class CircularArray[T](CircularArrayBase[T, IArray[T]], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], start: int):
        super().__init__(items, start)
class CircularList[T](CircularBase[T, IList[T]], List[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], start: int):
        super().__init__(items, start)
    
    @final
    def Add(self, item: T) -> None:
        index: int = self.GetIndex(self.GetLastIndex())

        self._GetContainer().Insert(index, item)

        self.Swap(index, index + 1)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self._GetContainer().TryInsert(self.GetIndex(index), value)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(self.GetIndex(index))
    
    @final
    def Clear(self) -> None:
        self._GetContainer().Clear()