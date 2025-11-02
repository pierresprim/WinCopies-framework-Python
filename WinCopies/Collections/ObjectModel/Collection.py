from abc import abstractmethod
from collections.abc import Iterable, Sequence
from typing import overload, final, SupportsIndex

from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Extensions import ITuple, IList, KeyableBase, MutableSequence
from WinCopies.Collections.Range import SetItems, RemoveItems
from WinCopies.Typing import IGenericConstraintImplementation, GenericConstraint
from WinCopies.Typing.Delegate import EqualityComparison

class __CollectionAbstractor[T](Sequence[T], KeyableBase[int, T], IList[T]):
    def __init__(self):
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class CollectionAbstractor[T](__CollectionAbstractor[T], MutableSequence[T]):
    def __init__(self):
        super().__init__()

class CollectionBase[TItem, TList](CollectionAbstractor[TItem], GenericConstraint[TList, IList[TItem]]):
    def __init__(self, items: TList):
        super().__init__()

        self.__items: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__items
    
    @abstractmethod
    def Duplicate(self, items: IList[TItem]) -> CollectionAbstractor[TItem]:
        pass

    @final
    def AsReversed(self) -> IList[TItem]:
        return self.Duplicate(self._GetInnerContainer().AsReversed())

    @final
    def AsReadOnly(self) -> ITuple[TItem]:
        return self._GetInnerContainer().AsReadOnly()
    
    def _SetItem(self, index: int, item: TItem) -> bool:
        return self._GetInnerContainer().TrySetAt(index, item)
    
    def _InsertItem(self, index: int|None, item: TItem) -> bool:
        if index is None:
            self._GetInnerContainer().Add(item)

            return True
        
        return self._GetInnerContainer().TryInsert(index, item)
    
    def _RemoveItemAt(self, index: int) -> bool|None:
        return self._GetInnerContainer().TryRemoveAt(index)
    
    def _ClearItems(self) -> None:
        self._GetInnerContainer().Clear()
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return self._GetInnerContainer().TryGetEnumerator()
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindLastIndex(item, predicate)
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._SetItem(key, value)
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]:
        return self._GetInnerContainer().SliceAt(key)
    
    @final
    def Add(self, item: TItem) -> None:
        self._InsertItem(None, item)
    @final
    def TryInsert(self, index: int, value: TItem) -> bool:
        return self._InsertItem(index, value)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        self._RemoveItemAt(index)
    
    @final
    def Clear(self) -> None:
        self._ClearItems()
    
    @final
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
    
    @final
    def insert(self, index: int, value: TItem) -> None:
        self.Insert(index, value)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None:
        SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice):
        RemoveItems(self, index)
@final
class Collection[T](CollectionBase[T, IList[T]], IList[T], IGenericConstraintImplementation[IList[T]]):
    def __init__(self, items: IList[T]):
        super().__init__(items)
    
    def Duplicate(self, items: IList[T]) -> CollectionAbstractor[T]:
        return Collection[T](items)