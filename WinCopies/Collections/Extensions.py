from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Container, Iterable, Iterator, Collection as CollectionBase, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, SupportsIndex

from WinCopies import Collections, Abstract, IStringable
from WinCopies.Collections import Enumeration, ICountableCollection, IReadOnlyCountableList, ICountableList as ICountableListBase, IGetter, ISetter, IndexOf
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEquatableEnumerable, IEnumerator, CountableEnumerable, GetIterator, TryAsIterator
from WinCopies.Typing import IGenericConstraint, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, INullable, IEquatableItem, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Method, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import IKeyValuePair

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsCollection(self) -> CollectionBase[T]:
        pass
    
    def AsSized(self) -> Sized:
        return self.AsCollection()
    def AsContainer(self) -> Container[T]:
        return self.AsCollection()
    def AsIterable(self) -> Iterable[T]:
        return self.AsCollection()

class IEnumerableCollection[T](IReadOnlyCollection[T], ICountableCollection[T]):
    def __init__(self) -> None:
        super().__init__()

class ICollection[T](IEnumerableCollection[T], ICountableListBase[T]):
    def __init__(self) -> None:
        super().__init__()

class ISequence[T](IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsSequence(self) -> SequenceBase[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsSequence()
    def AsContainer(self) -> Container[T]:
        return self.AsSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsSequence()
    def AsCollection(self) -> CollectionBase[T]:
        return self.AsSequence()
class IMutableSequence[T](ISequence[T], ICollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsMutableSequence(self) -> MutableSequenceBase[T]:
        pass

    def AsSized(self) -> Sized:
        return self.AsMutableSequence()
    def AsContainer(self) -> Container[T]:
        return self.AsMutableSequence()
    def AsIterable(self) -> Iterable[T]:
        return self.AsMutableSequence()
    def AsCollection(self) -> CollectionBase[T]:
        return self.AsMutableSequence()
    def AsSequence(self) -> SequenceBase[T]:
        return self.AsMutableSequence()

class ReadOnlyCollectionBase[T](CollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _TryGetIterator(self) -> Iterator[T]|None:
        return TryAsIterator(self.TryGetEnumerator())
    
    @final
    def __len__(self) -> int:
        return self.GetCount()
    
    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> CollectionBase[T]:
        return self
class ReadOnlyCollection[T](ReadOnlyCollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]:
        return GetIterator(self._TryGetIterator())

class ReadOnlySequence[T](SequenceBase[T], ReadOnlyCollectionBase[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    @final
    def __iter__(self) -> Iterator[T]:
        return GetIterator(self._TryGetIterator())

class Sequence[T](ReadOnlySequence[T], ISequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def AsSequence(self) -> SequenceBase[T]:
        return self

    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> CollectionBase[T]:
        return self
class MutableSequence[T](MutableSequenceBase[T], Sequence[T], IMutableSequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def AsMutableSequence(self) -> MutableSequenceBase[T]:
        return self

    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> CollectionBase[T]:
        return self
    def AsSequence(self) -> SequenceBase[T]:
        return self

class ITuple[T](Collections.ITuple[T], ISequence[T], IStringable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableItem](Collections.IEquatableTuple[T], ITuple[T], IEquatableEnumerable[T]):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def AsReversed(self) -> IArray[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IArray[T]:
        pass
class IList[T](Collections.IList[T], IArray[T], IMutableSequence[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        pass

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: IEquatableItem, TValue](Collections.IReadOnlyDictionary[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        pass
    @abstractmethod
    def GetValues(self) -> ICountableEnumerable[TValue]:
        pass
# TODO: Should implement a MutableMapping abstractor provider.
class IDictionary[TKey: IEquatableItem, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        pass

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, ICountableEnumerable[T], IStringable):
    def __init__(self) -> None:
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        pass

class _ReversedBase[TItem, TCollectionIn, TCollectionOut](SequenceBase[TItem], ITuple[TItem], GenericConstraint[TCollectionIn, ITuple[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        super().__init__()

        self.__items: TCollectionIn = items
    
    @final
    def _GetIndex(self, index: int) -> int:
        return self.GetCount() - index - 1
    
    @final
    def _GetContainer(self) -> TCollectionIn:
        return self.__items
    
    @final
    def _GetKey(self, key: slice) -> slice:
        start, stop, step = key.indices(self.GetCount())
        
        return slice(self._GetIndex(start), self._GetIndex(stop), step)
    
    @abstractmethod
    def _SliceAt(self, key: slice) -> TCollectionOut:
        pass

    @final
    def ToSlicedAt(self, key: slice) -> TCollectionOut:
        return self._SliceAt(self._GetKey(key))
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def GetCount(self) -> int:
        return self.GetCount()
    
    @final
    def TryGetValue(self, key: int) -> INullable[TItem]:
        return self._GetInnerContainer().TryGetValue(self._GetIndex(key))
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindLastIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int:
        return self._GetInnerContainer().FindFirstIndex(item, predicate)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None:
        return TupleEnumerator[TItem](self)
    
    @final
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
    
    @final
    def AsSequence(self) -> SequenceBase[TItem]:
        return self
class _Reversed[TItem, TCollection](_ReversedBase[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection) -> None:
        super().__init__(items)

class SequenceAbstract[T](Sequence[T], ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|SequenceBase[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()
class MutableSequenceAbstract[T](MutableSequence[T], IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsMutableSequence()

@final
class _ReadOnlyReversedTuple[T](_Reversed[T, ITuple[T]], SequenceAbstract[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)
    
    def _SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ITuple[T]:
        return self._GetContainer()

@final
class _ReadOnlyTupleUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: ITuple[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ITuple[T] = array
    
    def _GetValue(self) -> ITuple[T]:
        return _ReadOnlyReversedTuple[T](self.__array)

class _ReadOnlyTuple[T](Abstract, ITuple[T], IStringable):
    def __init__(self, items: IArray[T]) -> None:
        def update(func: IFunction[ITuple[T]]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__items: IArray[T] = items
        self.__reversed: IFunction[ITuple[T]] = _ReadOnlyTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IArray[T]:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetItems().IsEmpty()
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def TryGetValue(self, key: int) -> INullable[T]:
        return self._GetItems().TryGetValue(key)
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetItems().SliceAt(key)
    
    @final
    def Contains(self, value: T|object) -> bool:
        return self._GetItems().Contains(value)
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return self._GetItems().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return self._GetItems().FindLastIndex(item, predicate)
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetItems().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetItems().ToString()
    
    @final
    def AsReversed(self) -> ITuple[T]:
        return self.__reversed.GetValue()
    
    @final
    def AsSequence(self) -> SequenceBase[T]:
        return self._GetItems().AsSequence()

class _ReversedArrayBase[TItem, TCollectionIn, TCollectionOut](_ReversedBase[TItem, TCollectionIn, TCollectionOut], IArray[TItem], GenericSpecializedConstraint[TCollectionIn, ITuple[TItem], IArray[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        def update(func: IFunction[ITuple[TItem]]) -> None:
            self.__readOnly = func
        
        super().__init__(items)
        
        self.__readOnly: IFunction[ITuple[TItem]] = self._GetUpdater(update) # type: ignore[no-redef]
    
    @abstractmethod
    def _GetUpdater(self, func: Method[IFunction[ITuple[TItem]]]) -> ValueFunctionUpdater[ITuple[TItem]]:
        pass
    
    def TrySetAt(self, key: int, value: TItem) -> bool:
        return self._GetSpecializedContainer().TrySetAt(self._GetIndex(key), value)
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]:
        return self.__readOnly.GetValue()

class GetterBase[TKey, TValue](Abstract, IGetter[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetAt(self, key: TKey) -> TValue:
        pass
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        return GetNullable(self._GetAt(key)) if self.ContainsKey(key) else GetNullValue()
class SetterBase[TKey, TValue](Abstract, ISetter[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _SetAt(self, key: TKey, value: TValue) -> None:
        pass
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if self.ContainsKey(key):
            self._SetAt(key, value)

            return True
        
        return False

class KeyableBase[TKey, TValue](GetterBase[TKey, TValue], SetterBase[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()

class TupleEnumeratorBase[TItem, TList](Enumeration.EnumeratorBase[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()

        self.__list: TList = items
        self.__i: int = -1
    
    def _GetContainer(self) -> TList:
        return self.__list
    
    def IsResetSupported(self) -> bool:
        return True
    
    def _MoveNextOverride(self) -> bool:
        self.__i += 1
        
        return self.__i < self._GetInnerContainer().GetCount()
    
    def GetCurrent(self) -> TItem:
        return self._GetInnerContainer().GetAt(self.__i)
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        self.__i = -1

        return True
class TupleEnumerator[T](TupleEnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)

class TupleAbstract[T](Collections.Tuple[T], GetterBase[int, T], ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def __FindIndex(self, sequence: SequenceBase[T], item: T, predicate: EqualityComparison[T]|None) -> int:
        result: int|None = IndexOf(sequence, item, predicate)

        return -1 if result is None else result
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return self.__FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return self.__FindIndex(self.AsReversed().AsSequence(), item, predicate)
class TupleBase[T](TupleAbstract[T]):
    # Not final to allow customization of the enumerator.
    def TryGetEnumerator(self) -> IEnumerator[T]:
        return TupleEnumerator[T](self)

@final
class _ReversedTuple[T](_Reversed[T, ITuple[T]], SequenceAbstract[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T]) -> None:
        super().__init__(items)
    
    def _SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> ITuple[T]:
        return self._GetContainer()
@final
class __ReversedTupleUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: ITuple[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: ITuple[T] = array
    
    def _GetValue(self) -> ITuple[T]:
        return _ReversedTuple[T](self.__array)

@final
class _ReversedEquatableTuple[T: IEquatableItem](_Reversed[T, IEquatableTuple[T]], SequenceAbstract[T], IEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T]) -> None:
        super().__init__(items)
    
    def _SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self.ToSlicedAt(key)

    def AsReversed(self) -> IEquatableTuple[T]:
        return self._GetContainer()
    
    def Equals(self, item: object) -> bool:
        return self._GetContainer().Equals(item)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
@final
class _ReversedEquatableTupleUpdater[T: IEquatableItem](ValueFunctionUpdater[IEquatableTuple[T]]):
    def __init__(self, array: IEquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IEquatableTuple[T] = array
    
    def _GetValue(self) -> IEquatableTuple[T]:
        return _ReversedEquatableTuple[T](self.__array)

class TupleCollection[T](TupleAbstract[T]):
    def __init__(self) -> None:
        def update(func: IFunction[ITuple[T]]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[ITuple[T]] = __ReversedTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> ITuple[T]:
        return self.__reversed.GetValue()
class Tuple[T](TupleCollection[T], TupleBase[T]):
    def __init__(self) -> None:
        super().__init__()

class EquatableTupleCollection[T: IEquatableItem](TupleAbstract[T], IEquatableTuple[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IEquatableTuple[T]] = _ReversedEquatableTupleUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReversed(self) -> IEquatableTuple[T]:
        return self.__reversed.GetValue()
class EquatableTuple[T: IEquatableItem](EquatableTupleCollection[T], TupleBase[T], IEquatableTuple[T]):
    def __init__(self) -> None:
        super().__init__()

@final
class _ReadOnlyReversedArrayUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: IArray[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArray[T] = array
    
    def _GetValue(self) -> ITuple[T]:
        return _ReadOnlyTuple(self.__array)

class ReversedArrayAbstract[TItem, TCollectionIn, TCollectionOut](_ReversedArrayBase[TItem, TCollectionIn, TCollectionOut], IArray[TItem], IGenericConstraint[TCollectionIn, IArray[TItem]]):
    def __init__(self, items: TCollectionIn) -> None:
        super().__init__(items)
    
    @final
    def _GetUpdater(self, func: Method[IFunction[ITuple[TItem]]]) -> ValueFunctionUpdater[ITuple[TItem]]:
        return _ReadOnlyReversedArrayUpdater[TItem](self, func)
    
    @final
    def TrySetAt(self, key: int, value: TItem) -> bool:
        return self._GetSpecializedContainer().TrySetAt(self._GetIndex(key), value)
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._GetSpecializedContainer().Move(self._GetIndex(x), self._GetIndex(y))
class ReversedArray[TItem, TCollection](ReversedArrayAbstract[TItem, TCollection, TCollection]):
    def __init__(self, items: TCollection) -> None:
        super().__init__(items)

@final
class _ReversedArrayReadOnlyUpdater[T](ValueFunctionUpdater[ITuple[T]]):
    def __init__(self, array: IArray[T], updater: Method[IFunction[ITuple[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArray[T] = array
    
    def _GetValue(self) -> ITuple[T]:
        return _ReadOnlyTuple[T](self.__array)

class ArrayAbstract[TItem, TCollection](TupleAbstract[TItem], KeyableBase[int, TItem], IArray[TItem]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetUpdater(self, func: Method[IFunction[TCollection]]) -> IFunction[TCollection]:
        pass
class ArrayCollectionBase[TItem, TCollection](ArrayAbstract[TItem, TCollection]):
    def __init__(self) -> None:
        def updateReadOnly(func: IFunction[ITuple[TItem]]) -> None:
            self.__readOnly = func
        def updateReversed(func: IFunction[TCollection]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__readOnly: IFunction[ITuple[TItem]] = _ReversedArrayReadOnlyUpdater[TItem](self, updateReadOnly) # type: ignore[no-redef]
        self.__reversed: IFunction[TCollection] = self._GetUpdater(updateReversed) # type: ignore[no-redef]
    
    @final
    def _AsReversed(self) -> TCollection:
        return self.__reversed.GetValue()
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]:
        return self.__readOnly.GetValue()
class ArrayBase[TItem, TCollection](ArrayCollectionBase[TItem, TCollection], TupleBase[TItem]):
    def __init__(self) -> None:
        super().__init__()

@final
class _ReversedArray[T](ReversedArray[T, IArray[T]], SequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T]) -> None:
        super().__init__(items)

    @final
    def AsReversed(self) -> IArray[T]:
        return self._GetSpecializedContainer()
    
    @final
    def _SliceAt(self, key: slice) -> IArray[T]:
        return self._GetSpecializedContainer().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._AsSpecialized(self.ToSlicedAt(key))
@final
class _ReversedArrayUpdater[T](ValueFunctionUpdater[IArray[T]]):
    def __init__(self, array: IArray[T], updater: Method[IFunction[IArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: IArray[T] = array
    
    def _GetValue(self) -> IArray[T]:
        return _ReversedArray[T](self.__array)

class ArrayCollection[T](Collections.Array[T], ArrayCollectionBase[T, IArray[T]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _GetUpdater(self, func: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]:
        return _ReversedArrayUpdater[T](self, func)
    
    @final
    def AsReversed(self) -> IArray[T]:
        return self._AsReversed()
class Array[T](ArrayBase[T, IArray[T]], ArrayCollection[T]):
    def __init__(self) -> None:
        super().__init__()

class ReversedListAbstract[TItem, TListIn, TListOut](ReversedArrayAbstract[TItem, TListIn, TListOut], MutableSequence[TItem], IList[TItem]):
    def __init__(self, items: TListIn) -> None:
        super().__init__(items)
    
    @abstractmethod
    def _GetInnerContainerAsList(self, container: TListIn) -> IList[TItem]:
        pass
    @abstractmethod
    def _GetSpecializedContainerAsList(self, container: TListOut) -> IList[TItem]:
        pass

    @final
    def _GetContainerAsList(self) -> IList[TItem]:
        return self._GetInnerContainerAsList(self._GetContainer())
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]:
        return self._GetSpecializedContainerAsList(self.ToSlicedAt(key))
    
    def Add(self, item: TItem) -> None:
        if self.GetCount() > 0:
            self._GetContainerAsList().Insert(0, item)
        
        else:
            self._GetContainerAsList().Add(item)
    
    def TryInsert(self, index: int, value: TItem) -> bool:
        return self._GetContainerAsList().TryInsert(self._GetIndex(index), value)
    
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainerAsList().TryRemoveAt(self._GetIndex(index))
    
    def Clear(self) -> None:
        self._GetContainerAsList().Clear()

    def AsReversed(self) -> IList[TItem]:
        return self._GetContainerAsList()
    
    def AsMutableSequence(self) -> MutableSequenceBase[TItem]:
        return self
    
    def insert(self, index: int, value: TItem) -> None:
        return self._GetContainerAsList().AsMutableSequence().insert(self._GetIndex(index), value)

    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None:
        self._GetContainerAsList().AsMutableSequence()[self._GetIndex(int(index)) if isinstance(index, SupportsIndex) else self._GetKey(index)] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        del self._GetContainerAsList().AsMutableSequence()[self._GetIndex(index) if isinstance(index, int) else self._GetKey(index)]
class ReversedListBase[TItem, TList](ReversedListAbstract[TItem, TList, TList]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)

@final
class _ReversedList[T](ReversedListBase[T, IList[T]], MutableSequenceAbstract[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T]) -> None:
        super().__init__(items)
    
    def _GetInnerContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    @final
    def _GetSpecializedContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainerAsList().SliceAt(key)
@final
class _ReversedListUpdater[T](ValueFunctionUpdater[IList[T]]):
    def __init__(self, array: Collection[T], updater: Method[IFunction[IList[T]]]) -> None:
        super().__init__(updater)

        self.__array: Collection[T] = array
    
    def _GetValue(self) -> IList[T]:
        return _ReversedList[T](self.__array)

class Collection[T](Collections.List[T], ArrayCollectionBase[T, IList[T]], IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _GetUpdater(self, func: Method[IFunction[IList[T]]]) -> IFunction[IList[T]]:
        return _ReversedListUpdater[T](self, func)
    
    @final
    def AsReversed(self) -> IList[T]:
        return self._AsReversed()
class List[T](ArrayBase[T, IList[T]], Collection[T]):
    def __init__(self) -> None:
        super().__init__()

class _ReadOnlySet[T: IEquatableItem](CountableEnumerable[T], IReadOnlySet[T]):
    def __init__(self, items: IReadOnlySet[T]) -> None:
        super().__init__()

        self.__set: IReadOnlySet[T] = items
    
    @final
    def _GetItems(self) -> IReadOnlySet[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return Enumerator[T].TryCreate(self._GetItems().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetItems().ToString()
@final
class _ReadOnlySetUpdater[T: IEquatableItem](ValueFunctionUpdater[IReadOnlySet[T]]):
    def __init__(self, items: Set[T], updater: Method[IFunction[IReadOnlySet[T]]]) -> None:
        super().__init__(updater)

        self.__items: Set[T] = items
    
    def _GetValue(self) -> IReadOnlySet[T]:
        return _ReadOnlySet[T](self.__items)

class Set[T: IEquatableItem](CountableEnumerable[T], ISet[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlySet[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlySet[T]] = _ReadOnlySetUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlySet[T]:
        return self.__readOnly.GetValue()

class _ReadOnlyDictionary[TKey: IEquatableItem, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IReadOnlyDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    def __init__(self, dictionary: Dictionary[TKey, TValue]) -> None:
        super().__init__()

        self.__dictionary: Dictionary[TKey, TValue] = dictionary
    
    @final
    def _GetDictionary(self) -> Dictionary[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int:
        return self._GetDictionary().GetCount()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self._GetDictionary().ContainsKey(key)
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        return self._GetDictionary().TryGetValue(key)
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        return self._GetDictionary().GetKeys()
    @final
    def GetValues(self) -> ICountableEnumerable[TValue]:
        return self._GetDictionary().GetValues()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]|None:
        return Enumerator[IKeyValuePair[TKey, TValue]].TryCreate(self._GetDictionary().TryGetEnumerator())
    
    def ToString(self) -> str:
        return self._GetDictionary().ToString()
@final
class _ReadOnlyDictionaryUpdater[TKey: IEquatableItem, TValue](ValueFunctionUpdater[IReadOnlyDictionary[TKey, TValue]]):
    def __init__(self, dictionary: Dictionary[TKey, TValue], updater: Method[IFunction[IReadOnlyDictionary[TKey, TValue]]]) -> None:
        super().__init__(updater)

        self.__dictionary: Dictionary[TKey, TValue] = dictionary
    
    def _GetValue(self) -> IReadOnlyDictionary[TKey, TValue]:
        return _ReadOnlyDictionary[TKey, TValue](self.__dictionary)

class Dictionary[TKey: IEquatableItem, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyDictionary[TKey, TValue]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyDictionary[TKey, TValue]] = _ReadOnlyDictionaryUpdater[TKey, TValue](self, update) # type: ignore[no-redef]
    
    @final
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        return self.__readOnly.GetValue()
    
    def Move(self, x: TKey, y: TKey) -> None:
        def getValue() -> TValue:
            value: INullable[TValue] = self.TryRemoveItem(x)

            if value.HasValue():
                return value.GetValue()
            
            raise KeyError(f"The key {x} does not exist.")

        self.Add(y, getValue())