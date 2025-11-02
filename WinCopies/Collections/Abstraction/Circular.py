from typing import final

from WinCopies.Collections.Circular import ICircularTuple, ICircularEquatableTuple, ICircularArray, ICircularList
from WinCopies.Collections.Extensions import TupleBase, ArrayBase, Sequence, MutableSequence, Tuple, EquatableTuple
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, IEquatableItem

class CircularBase[TItem, TList](TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], GenericConstraint[TList, ICircularTuple[TItem]]):
    def __init__(self, items: TList):
        super().__init__()
        
        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        return self._GetInnerContainer().GetStart()
    
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()

class CircularTuple[T](CircularBase[T, ICircularTuple[T]], Tuple[T], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: ICircularTuple[T]):
        super().__init__(items)
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, ICircularEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T]):
        super().__init__(items)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], ArrayBase[TItem, TList], ICircularArray[TItem], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(key, value)
class CircularArray[T](CircularArrayBase[T, ICircularArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T]):
        super().__init__(items)
class CircularList[T](CircularArrayBase[T, ICircularList[T]], MutableSequence[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T]):
        super().__init__(items)
    
    @final
    def Add(self, item: T) -> None:
        self._GetContainer().Add(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self._GetContainer().TryInsert(index, value)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(index)
    
    @final
    def Clear(self) -> None:
        self._GetContainer().Clear()