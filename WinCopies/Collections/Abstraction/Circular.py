from typing import final

from WinCopies.Collections.Circular import ICircularTuple, ICircularEquatableTuple, ICircularArray, ICircularList
from WinCopies.Collections.Extensions import Tuple, EquatableTuple, Array, List
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, IEquatableItem
from WinCopies.Typing.Delegate import EqualityComparison

class CircularBase[TItem, TList](GenericConstraint[TList, ICircularTuple[TItem]], ICircularTuple[TItem]):
    def __init__(self, items: TList):
        super().__init__()
        
        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        return self._GetInnerContainer().GetStart()
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()

class CircularTuple[T](CircularBase[T, ICircularTuple[T]], Tuple[T], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: ICircularTuple[T]):
        super().__init__(items)
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, ICircularEquatableTuple[T]], EquatableTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T]):
        super().__init__(items)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @final
    def SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(key, value)
class CircularArray[T](CircularArrayBase[T, ICircularArray[T]], Array[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T]):
        super().__init__(items)
class CircularList[T](CircularBase[T, ICircularList[T]], List[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T]):
        super().__init__(items)
    
    @final
    def Add(self, item: T) -> None:
        self._GetContainer().Add(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self._GetContainer().TryInsert(index, value)
    
    @final
    def RemoveAt(self, index: int) -> None:
        self._GetContainer().RemoveAt(index)
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(index)
    
    @final
    def TryRemove(self, item: T, predicate: EqualityComparison[T]|None = None) -> bool:
        return self._GetContainer().TryRemove(item, predicate)
    @final
    def Remove(self, item: T, predicate: EqualityComparison[T]|None = None) -> None:
        self._GetContainer().Remove(item, predicate)
    
    @final
    def Clear(self) -> None:
        self._GetContainer().Clear()