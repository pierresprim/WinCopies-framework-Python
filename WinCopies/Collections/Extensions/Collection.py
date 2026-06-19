from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase
from typing import overload, final, SupportsIndex



from WinCopies import IInterface, Abstract

from WinCopies.Collections.Abstraction.Enumeration import TryCreateEnumerator, TryCreateResumableEnumerator
from WinCopies.Collections.Core import Mutability, IIndexableCollectionBase, IGetter, ISetter, Tuple as _Tuple, Array as _Array, List as _List, SortedList as _SortedList
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import ICollection, IResumableEnumeratorMonitor, ITuple, ISortedTuple, IEquatableTuple, IHashableTuple, IArrayBase, IArray, IListBase, IList, ISortedList, SequenceAbstract, MutableSequenceAbstract, Sequence, MutableSequence
from WinCopies.Collections.Extensions.Enumeration import IResumableEnumeratorFactory, ResumableEnumeratorFactory, TupleEnumerator, ResumableTupleEnumerator
from WinCopies.Collections.Iteration.Extensions import Reverse
from WinCopies.Collections.ObjectModel import ReadOnlyCollection, SortedCollection as SortedCollectionBase, FixedSizeCollection
from WinCopies.Collections.Util import FindIndex

from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Comparison import IEquatableValue, IHashableValue, INotHashableValue
from WinCopies.Typing.Delegate import Method, Converter, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Protocols import SupportsRichComparison

class _ReversedAbstract[TItem, TCollectionIn, TCollectionOut](SequenceBase[TItem], ITuple[TItem], GenericConstraint[TCollectionIn, ITuple[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        super().__init__()

        self.__items: TCollectionIn = items
    
    @final
    def _GetContainer(self) -> TCollectionIn: return self.__items
    
    @abstractmethod
    def _SliceAt(self, key: slice) -> TCollectionOut:
        ...

    @final
    def ToSlicedAt(self, key: slice) -> TCollectionOut:
        return self._SliceAt(self.ReverseKey(key))
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def TryGetValue(self, key: int) -> INullable[TItem]: return self._GetInnerContainer().TryGetValue(self.ReverseIndex(key))
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindLastIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindFirstIndex(item, predicate)
    
    @final
    def ToString(self) -> str: return self._GetInnerContainer().ToString()
class _ReversedBase[TItem, TCollectionIn, TCollectionOut](_ReversedAbstract[TItem, TCollectionIn, TCollectionOut]):
    def __init__(self, items: TCollectionIn, factory: IResumableEnumeratorMonitor[TItem]) -> None:
        super().__init__(items)

        self.__factory: IResumableEnumeratorMonitor[TItem] = factory
    
    @final
    def _GetFactory(self) -> IResumableEnumeratorMonitor[TItem]:
        return self.__factory
    
    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[TItem]: return self.__factory
    
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().TryGetSourceMutability()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return self.__factory.CreateEnumerator(self)
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]|None: return self.__factory.CreateResumableEnumerator(self)

class _Reversed[TItem, TCollection](_ReversedBase[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)

@final
class _ReversedTuple[T](_Reversed[T, ITuple[T]], SequenceAbstract[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], factory: IResumableEnumeratorMonitor[T]) -> None: super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def _SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ITuple[T]: return self._GetContainer()
@final
class _ReversedTupleUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: ITuple[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ITuple[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ITuple[T]: return _ReversedTuple[T](self.__array, self.__factory)

@final
class _ReversedSortedTuple[T](_Reversed[T, ISortedTuple[T]], SequenceAbstract[T], ISortedTuple[T], IGenericConstraintImplementation[ISortedTuple[T]]):
    def __init__(self, items: ISortedTuple[T], factory: IResumableEnumeratorMonitor[T]) -> None: super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectLeft(item, converter)
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectRight(item, converter)
    
    def _SliceAt(self, key: slice) -> ISortedTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ISortedTuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ISortedTuple[T]: return self._GetContainer()
@final
class _ReversedSortedTupleUpdater[T](ValueFunctionUpdater[ISortedTuple[T]]):
    def __init__(self, array: ISortedTuple[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ISortedTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedTuple[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ISortedTuple[T]: return _ReversedSortedTuple[T](self.__array, self.__factory)

class _IReadOnlyTuple[TItem, TList](ITuple[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().TryGetSourceMutability()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return TryCreateEnumerator(self._GetInnerContainer().TryGetEnumerator())
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]|None: return TryCreateResumableEnumerator(self._GetInnerContainer().TryGetResumableEnumerator())

class _ReadOnlyTuple[T](ReadOnlyCollection[T], _IReadOnlyTuple[T, ITuple[T]]):
    def __init__(self, items: IArrayBase[T], factory: IResumableEnumeratorMonitor[T]) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__factory: IResumableEnumeratorMonitor[T] = factory
        self.__reversed: IFunction[ITuple[T]] = _ReversedTupleUpdater[T](self, factory, update) # type: ignore[no-redef]
    
    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]: return self.__factory
    
    @final
    def AsReversed(self) -> ITuple[T]: return self.__reversed.GetValue()
class _ReadOnlySortedTuple[T](SortedCollectionBase[T], _IReadOnlyTuple[T, ISortedTuple[T]]):
    def __init__(self, items: ISortedList[T], factory: IResumableEnumeratorMonitor[T]) -> None:
        def update(func: IFunction[ISortedTuple[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__factory: IResumableEnumeratorMonitor[T] = factory
        self.__reversed: IFunction[ISortedTuple[T]] = _ReversedSortedTupleUpdater[T](self, factory, update) # type: ignore[no-redef]
    
    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]: return self.__factory
    
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectLeft(item, converter)
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectRight(item, converter)
    
    @final
    def AsReversed(self) -> ISortedTuple[T]: return self.__reversed.GetValue()

class GetterBase[TKey, TValue](Abstract, IGetter[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetAt(self, key: TKey) -> TValue:
        pass
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]: return GetNullable(self._GetAt(key)) if self.ContainsKey(key) else GetNullValue()
class SetterBase[TKey, TValue](Abstract, ISetter[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _SetAt(self, key: TKey, value: TValue) -> None:
        ...
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if self.ContainsKey(key):
            self._SetAt(key, value)

            return True
        
        return False

class KeyableBase[TKey, TValue](GetterBase[TKey, TValue], SetterBase[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class TupleAbstractBase[T](GetterBase[int, T], _Tuple[T], ITuple[T]):
    def __init__(self) -> None: super().__init__()
class TupleAbstract[T](TupleAbstractBase[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return FindIndex(self.AsReversed().AsSequence(), item, predicate)

class _ITuple[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetEnumeratorFactory(self) -> IResumableEnumeratorFactory[T]:
        ...

    @final
    def _InvalidateEnumerators(self) -> None:
        self._GetEnumeratorFactory().InvalidateObjects()

class _TupleBase[T](TupleAbstractBase[T], _ITuple[T]):
    def __init__(self) -> None: super().__init__()
    
    # Not final to allow customization of the enumerator.
    def _TryGetEnumerator(self) -> IEnumerator[T]:
        return TupleEnumerator[T](self)
    def _TryGetResumableEnumerator(self) -> IResumableEnumerator[T]:
        return ResumableTupleEnumerator[T](self)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]:
        enumerator: IEnumerator[T] = self._TryGetEnumerator()

        self._GetEnumeratorFactory().RegisterObject(enumerator)

        return enumerator
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]:
        enumerator: IResumableEnumerator[T] = self._TryGetResumableEnumerator()

        self._GetEnumeratorFactory().RegisterObject(enumerator)

        return enumerator
class TupleBase[T](_TupleBase[T], TupleAbstract[T]):
    def __init__(self) -> None: super().__init__()

@final
class _ReversedEquatableTuple[T: IEquatableValue](_Reversed[T, IEquatableTuple[T]], SequenceAbstract[T], IEquatableTuple[T], INotHashableValue, IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], factory: IResumableEnumeratorFactory[T]) -> None: super().__init__(items, factory)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    def _SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self.ToSlicedAt(key)
    
    def Equals(self, item: object) -> bool: return self._GetContainer().Equals(item)

    def AsReversed(self) -> IEquatableTuple[T]: return self._GetContainer()
@final
class _ReversedHashableTuple[T: IHashableValue](_Reversed[T, IHashableTuple[T]], SequenceAbstract[T], IHashableTuple[T], IGenericConstraintImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T], factory: IResumableEnumeratorFactory[T]) -> None: super().__init__(items, factory)
    
    def _SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self.ToSlicedAt(key)
    
    def Equals(self, item: object) -> bool: return self._GetContainer().Equals(item)
    def Hash(self) -> int: return self._GetContainer().Hash()

    def AsReversed(self) -> IHashableTuple[T]: return self._GetContainer()
@final
class _ReversedEquatableTupleUpdater[T: IEquatableValue](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, array: IEquatableTuple[T], factory: IResumableEnumeratorFactory[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IEquatableTuple[T] = array
        self.__factory: IResumableEnumeratorFactory[T] = factory
    
    def _GetValue(self) -> IEquatableTuple[T]: return _ReversedEquatableTuple[T](self.__array, self.__factory)
@final
class _ReversedHashableTupleUpdater[T: IHashableValue](ValueFunctionUpdater[IHashableTuple[T]]):
    def __init__(self, array: IHashableTuple[T], factory: IResumableEnumeratorFactory[T], updater: Method[IFunction[IHashableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IHashableTuple[T] = array
        self.__factory: IResumableEnumeratorFactory[T] = factory
    
    def _GetValue(self) -> IHashableTuple[T]: return _ReversedHashableTuple[T](self.__array, self.__factory)

class _TupleCollection[T](TupleAbstract[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__factory: IResumableEnumeratorFactory[T] = ResumableEnumeratorFactory[T]()
    
    @final
    def _GetEnumeratorFactory(self) -> IResumableEnumeratorFactory[T]:
        return self.__factory
    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]:
        return self._GetEnumeratorFactory().AsMonitor()

class TupleCollection[T](_TupleCollection[T]):
    def __init__(self) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[ITuple[T]] = _ReversedTupleUpdater[T](self, self._GetEnumeratorFactory(), update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> ITuple[T]: return self.__reversed.GetValue()
class Tuple[T](TupleCollection[T], TupleBase[T]):
    def __init__(self) -> None: super().__init__()

class EquatableTupleCollection[T: IEquatableValue](_TupleCollection[T], IEquatableTuple[T], INotHashableValue):
    def __init__(self) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IEquatableTuple[T]] = _ReversedEquatableTupleUpdater[T](self, self._GetEnumeratorFactory(), update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IEquatableTuple[T]: return self.__reversed.GetValue()
class EquatableTuple[T: IEquatableValue](EquatableTupleCollection[T], TupleBase[T], IEquatableTuple[T]):
    def __init__(self) -> None: super().__init__()

class HashableTupleCollection[T: IHashableValue](_TupleCollection[T], IHashableTuple[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IHashableTuple[T]]) -> None: self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IHashableTuple[T]] = _ReversedHashableTupleUpdater[T](self, self._GetEnumeratorFactory(), update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IHashableTuple[T]: return self.__reversed.GetValue()
class HashableTuple[T: IHashableValue](HashableTupleCollection[T], TupleBase[T], IHashableTuple[T]):
    def __init__(self) -> None: super().__init__()

@final
class _ReadOnlyReversedArrayUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: IArrayBase[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArrayBase[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ITuple[T]: return _ReadOnlyTuple[T](self.__array, self.__factory)
@final
class _ReadOnlyReversedSortedArrayUpdater[T](ValueFunctionUpdater[ISortedTuple[T]]):
    def __init__(self, array: ISortedList[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ISortedTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedList[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ISortedTuple[T]: return _ReadOnlySortedTuple[T](self.__array, self.__factory)

class ReversedArrayAbstract[TItem, TCollectionIn, TCollectionOut](_ReversedBase[TItem, TCollectionIn, TCollectionOut], IArrayBase[TItem]):
    def __init__(self, items: TCollectionIn, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)
class ReversedArrayBase[TItem, TCollectionIn, TCollectionOut](ReversedArrayAbstract[TItem, TCollectionIn, TCollectionOut], IArray[TItem], GenericSpecializedConstraint[TCollectionIn, ITuple[TItem], IArray[TItem]]):
    def __init__(self, items: TCollectionIn, factory: IResumableEnumeratorMonitor[TItem]) -> None:
        def update(func: IFunction[ITuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__(items, factory)
        
        self.__readOnly: IFunction[ITuple[TItem]] = _ReadOnlyReversedArrayUpdater[TItem](self, self._GetFactory(), update) # type: ignore[no-redef]
    
    @final
    def TrySetAt(self, key: int, value: TItem) -> bool: return self._GetSpecializedContainer().TrySetAt(self.ReverseIndex(key), value)
    
    @final
    def Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(self.ReverseIndex(x), self.ReverseIndex(y))
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]: return self.__readOnly.GetValue()
class ReversedArray[TItem, TCollection](ReversedArrayBase[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)

class IArrayAbstract[TItem, TCollection](IArrayBase[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[TItem], func: Method[IFunction[TCollection]]) -> IFunction[TCollection]:
        ...
class ArrayAbstractBase[TItem, TCollection](TupleAbstractBase[TItem], GetterBase[int, TItem], IArrayAbstract[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()
class ArrayAbstract[TItem, TCollection](ArrayAbstractBase[TItem, TCollection], KeyableBase[int, TItem], TupleAbstract[TItem], IArray[TItem], _ITuple[TItem]):
    def __init__(self) -> None: super().__init__()

class _ArrayCollectionAbstract[TItem, TCollection](ArrayAbstractBase[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReversed(func: IFunction[TCollection]) -> None: self.__reversed = func
        
        super().__init__()

        factory: IResumableEnumeratorFactory[TItem] = ResumableEnumeratorFactory[TItem]()

        self.__factory: IResumableEnumeratorFactory[TItem] = factory
        self.__reversed: IFunction[TCollection] = self._GetUpdater(factory, updateReversed) # type: ignore[no-redef]
    
    @final
    def _GetEnumeratorFactory(self) -> IResumableEnumeratorFactory[TItem]:
        return self.__factory
    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[TItem]:
        return self._GetEnumeratorFactory().AsMonitor()
    
    @final
    def _AsReversed(self) -> TCollection:
        return self.__reversed.GetValue()
class _ArrayCollectionBase[TItem, TCollection](_ArrayCollectionAbstract[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ITuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[ITuple[TItem]] = _ReadOnlyReversedArrayUpdater[TItem](self, self._GetEnumeratorFactory(), updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]: return self.__readOnly.GetValue()
class ArrayCollectionBase[TItem, TCollection](_ArrayCollectionBase[TItem, TCollection], ArrayAbstract[TItem, TCollection]):
    def __init__(self) -> None: super().__init__()

class _ArrayAbstract[TItem, TCollection](_ArrayCollectionAbstract[TItem, TCollection], _TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()
class _ArrayBase[TItem, TCollection](_ArrayCollectionBase[TItem, TCollection], _TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()
class ArrayBase[TItem, TCollection](_ArrayBase[TItem, TCollection], ArrayCollectionBase[TItem, TCollection], TupleBase[TItem]):
    def __init__(self) -> None: super().__init__()

@final
class _ReversedArray[T](ReversedArray[T, IArray[T]], SequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], factory: IResumableEnumeratorMonitor[T]) -> None: super().__init__(items, factory)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def AsReversed(self) -> IArray[T]: return self._GetSpecializedContainer()
    
    @final
    def _SliceAt(self, key: slice) -> IArray[T]:
        return self._GetSpecializedContainer().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._AsSpecialized(self.ToSlicedAt(key))
@final
class _ReversedArrayUpdater[T](ValueFunctionUpdater[IArray[T]]):
    def __init__(self, array: IArray[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[IArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArray[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> IArray[T]: return _ReversedArray[T](self.__array, self.__factory)

class ArrayCollection[T](_Array[T], ArrayCollectionBase[T, IArray[T]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[T], func: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]:
        return _ReversedArrayUpdater[T](self, factory, func)
    
    @final
    def AsReversed(self) -> IArray[T]: return self._AsReversed()
class Array[T](ArrayBase[T, IArray[T]], ArrayCollection[T]):
    def __init__(self) -> None: super().__init__()

class _IIndexableCollectionAbstract[T](IIndexableCollectionBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetContainerAsList(self) -> IListBase[T]:
        ...
class _IReversedCollectionAbstract[T](_IIndexableCollectionAbstract[T], ICollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainerAsList().TryRemoveAt(self.ReverseIndex(index))
    
    @final
    def Clear(self) -> None: self._GetContainerAsList().Clear()

class ReversedCollectionAbstract[TItem, TList](ReversedArrayAbstract[TItem, TList, TList], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TList, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IListBase[TItem]:
        ...

    def AsReversed(self) -> IListBase[TItem]: return self._GetContainerAsList()
class ReversedCollectionBase[TItem, TListIn, TListOut](ReversedArrayBase[TItem, TListIn, TListOut], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TListIn, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)

    @abstractmethod
    def _GetContainerAsList(self) -> IList[TItem]:
        ...
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[TItem]:
        ...

    def AsReversed(self) -> IList[TItem]: return self._GetContainerAsList()
class ReversedCollection[TItem, TList](ReversedArray[TItem, TList], _IReversedCollectionAbstract[TItem]):
    def __init__(self, items: TList, factory: IResumableEnumeratorFactory[TItem]) -> None: super().__init__(items, factory)

@final
class _FixedSizeArray[T](FixedSizeCollection[T], IArray[T]):
    def __init__(self, items: IList[T], factory: IResumableEnumeratorMonitor[T]) -> None:
        def update(func: IFunction[IArray[T]]) -> None: self.__reversed = func
        
        super().__init__(items)

        self.__factory: IResumableEnumeratorMonitor[T] = factory
        self.__reversed: IFunction[IArray[T]] = _ReversedArrayUpdater[T](self, factory, update) # type: ignore[no-redef]
    
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetContainer().TryGetSourceMutability()
    
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor[T]: return self.__factory
    
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self._GetContainer().TryGetEnumerator()
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self._GetContainer().TryGetResumableEnumerator()
    
    def AsReversed(self) -> IArray[T]: return self.__reversed.GetValue()
@final
class _FixedSizeArrayUpdater[T](ValueFunctionUpdater[IArray[T]]):
    def __init__(self, items: IList[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[IArray[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[T] = items
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> IArray[T]: return _FixedSizeArray[T](self.__items, self.__factory)

class MutableList[T](MutableSequence[T], IList[T]):
    def __init__(self, ) -> None: super().__init__()

    @final
    def _GetReversedUpdater(self, factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]:
        return _FixedSizeArrayUpdater[T](self, factory, updater)

class ReversedListAbstract[TItem, TListIn, TListOut](ReversedCollectionBase[TItem, TListIn, TListOut], MutableList[TItem]):
    def __init__(self, items: TListIn, factory: IResumableEnumeratorMonitor[TItem]) -> None:
        def update(func: IFunction[IArray[TItem]]) -> None: self.__fixedSize = func
        
        super().__init__(items, factory)

        self.__fixedSize: IFunction[IArray[TItem]] = self._GetReversedUpdater(factory, update) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetInnerContainerAsList(self, container: TListIn) -> IList[TItem]:
        ...

    @final
    def _GetContainerAsList(self) -> IList[TItem]:
        return self._GetInnerContainerAsList(self._GetContainer())

    @final
    def AsFixedSize(self) -> IArray[TItem]: return self.__fixedSize.GetValue()
    @final
    def AsReversed(self) -> IList[TItem]: return self._GetContainerAsList()
    
    @final
    def Add(self, item: TItem) -> None:
        items: IList[TItem] = self._GetContainerAsList()

        if self.GetCount() > 0: items.Insert(0, item)
        else: items.Add(item)
    
    @final
    def TryInsert(self, index: int, value: TItem) -> bool: return self._GetContainerAsList().TryInsert(self.ReverseIndex(index), value)
    @final
    def TryInsertRange(self, index: int, items: Iterable[TItem]) -> bool:
        if self.ValidateIndex(index):
            _items: IList[TItem] = self._GetContainerAsList()
            items = Reverse(items)

            if index > 0: return _items.TryInsertRange(self.ReverseIndex(index), items)
            
            _items.AddRange(items)

            return True
        
        return False
    
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool: return self._GetContainerAsList().TryRemoveRange(self.ReverseRangeStartIndex(index, count), count)
    
    @final
    def insert(self, index: int, value: TItem) -> None: return self._GetContainerAsList().AsMutableSequence().insert(self.ReverseIndex(index), value)

    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None: self._GetContainerAsList().AsMutableSequence()[self.ReverseIndex(int(index)) if isinstance(index, SupportsIndex) else self.ReverseKey(index)] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None: del self._GetContainerAsList().AsMutableSequence()[self.ReverseIndex(index) if isinstance(index, int) else self.ReverseKey(index)]
class ReversedListBase[TItem, TList](ReversedListAbstract[TItem, TList, TList]):
    def __init__(self, items: TList, factory: IResumableEnumeratorMonitor[TItem]) -> None: super().__init__(items, factory)
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]: return self._GetInnerContainerAsList(self.ToSlicedAt(key))

class ReversedSortedListAbstract[TItem, TList](ReversedCollectionAbstract[TItem, TList], Sequence[TItem], ISortedList[TItem]):
    def __init__(self, items: TList, factory: IResumableEnumeratorMonitor[TItem]) -> None:
        def update(func: IFunction[ISortedTuple[TItem]]) -> None: self.__readOnly = func
        
        super().__init__(items, factory)
        
        self.__readOnly: IFunction[ISortedTuple[TItem]] = _ReadOnlyReversedSortedArrayUpdater[TItem](self, self._GetFactory(), update) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetInnerContainerAsList(self, container: TList) -> ISortedList[TItem]:
        ...
    @abstractmethod
    def _GetSpecializedContainerAsList(self, container: TList) -> ISortedList[TItem]:
        ...

    @final
    def _GetContainerAsList(self) -> ISortedList[TItem]:
        return self._GetInnerContainerAsList(self._GetContainer())
    
    @final
    def AddLeft(self, item: TItem) -> None: self._GetContainerAsList().Add(item)
    @final
    def Add(self, item: TItem) -> None: self._GetContainerAsList().AddLeft(item)
    
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool: return self._GetContainerAsList().TryRemoveRange(self.ReverseRangeStartIndex(index, count), count)
    
    @final
    def SliceAt(self, key: slice) -> ISortedList[TItem]: return self._GetSpecializedContainerAsList(self.ToSlicedAt(key))

    @final
    def AsReversed(self) -> ISortedList[TItem]: return self._GetContainerAsList()
    
    @final
    def AsReadOnly(self) -> ISortedTuple[TItem]: return self.__readOnly.GetValue()

@final
class _ReversedList[T](ReversedListBase[T, IList[T]], MutableSequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], factory: IResumableEnumeratorMonitor[T]) -> None: super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    def _GetInnerContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    def _GetSpecializedContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainerAsList().SliceAt(key)
@final
class _ReversedListUpdater[T](ValueFunctionUpdater[IList[T]]):
    def __init__(self, array: IList[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[IList[T]]]) -> None:
        super().__init__(updater)

        self.__array: IList[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> IList[T]: return _ReversedList[T](self.__array, self.__factory)

@final
class _ReversedSortedList[T](ReversedSortedListAbstract[T, ISortedList[T]], SequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], ISortedList[T]]):
    def __init__(self, items: ISortedList[T], factory: IResumableEnumeratorMonitor[T]) -> None: super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectRight(item, converter)
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return self._GetContainer().BisectLeft(item, converter)
    
    def _GetInnerContainerAsList(self, container: ISortedList[T]) -> ISortedList[T]:
        return container
    def _GetSpecializedContainerAsList(self, container: ISortedList[T]) -> ISortedList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> ISortedList[T]:
        return self._GetContainerAsList().SliceAt(key)
@final
class _ReversedSortedListUpdater[T](ValueFunctionUpdater[ISortedList[T]]):
    def __init__(self, array: ISortedList[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ISortedList[T]]]) -> None:
        super().__init__(updater)

        self.__array: ISortedList[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ISortedList[T]: return _ReversedSortedList[T](self.__array, self.__factory)

class CollectionAbstract[T](IArrayAbstract[T, IList[T]], IList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[T], func: Method[IFunction[IList[T]]]) -> IFunction[IList[T]]: return _ReversedListUpdater[T](self, factory, func)

class Collection[T](_List[T], ArrayCollectionBase[T, IList[T]], CollectionAbstract[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IArray[T]]) -> None: self.__fixedSize = func
        
        super().__init__()

        self.__fixedSize: IFunction[IArray[T]] = _FixedSizeArrayUpdater[T](self, self._GetEnumeratorFactory(), update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IList[T]: return self._AsReversed()
    
    @final
    def AsFixedSize(self) -> IArray[T]: return self.__fixedSize.GetValue()
class SortedCollection[T](_SortedList[T], _ArrayCollectionAbstract[T, ISortedList[T]], ISortedList[T]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ISortedTuple[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[ISortedTuple[T]] = _ReadOnlyReversedSortedArrayUpdater[T](self, self._GetEnumeratorFactory(), updateReadOnly) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> ISortedTuple[T]: return self.__readOnly.GetValue()
    
    @final
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[T], func: Method[IFunction[ISortedList[T]]]) -> IFunction[ISortedList[T]]: return _ReversedSortedListUpdater[T](self, factory, func)
    
    @final
    def AsReversed(self) -> ISortedList[T]: return self._AsReversed()

class List[T](ArrayBase[T, IList[T]], Collection[T]):
    def __init__(self) -> None: super().__init__()
class SortedList[T](_ArrayAbstract[T, ISortedList[T]], SortedCollection[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    @final
    def TryGetSourceMutability(self) -> None: return None