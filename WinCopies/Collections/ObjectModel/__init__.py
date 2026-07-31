from typing import final

from WinCopies.Collections.Extensions import ITuple, ISortedTuple, IArray, SequenceAbstract
from WinCopies.Typing import INullable
from WinCopies.Typing.Delegate import EqualityComparison
from WinCopies.Typing.Generic import GenericConstraint, IGenericConstraintImplementation

class ReadOnlyCollectionBase[TItem, TList](SequenceAbstract[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__items
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def TryGetValue(self, key: int) -> INullable[TItem]: return self._GetInnerContainer().TryGetValue(key)
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindLastIndex(item, predicate)
    
    @final
    def ToString(self) -> str: return self._GetInnerContainer().ToString()

class ReadOnlyCollection[T](ReadOnlyCollectionBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None: super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(key)

class SortedCollection[T](ReadOnlyCollectionBase[T, ISortedTuple[T]], ISortedTuple[T], IGenericConstraintImplementation[ISortedTuple[T]]):
    def __init__(self, items: ISortedTuple[T]) -> None: super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ISortedTuple[T]: return self._GetContainer().SliceAt(key)
class FixedSizeCollection[T](ReadOnlyCollectionBase[T, IArray[T]], IGenericConstraintImplementation[IArray[T]]):
    def __init__(self, items: IArray[T]) -> None: super().__init__(items)
    
    @final
    def Move(self, x: int, y: int) -> None: return self._GetContainer().Move(x, y)
    
    @final
    def TrySetAt(self, key: int, value: T) -> bool: return self._GetContainer().TrySetAt(key, value)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return self._GetContainer().SliceAt(key)
    
    @final
    def AsReadOnly(self) -> ITuple[T]: return self._GetContainer().AsReadOnly()