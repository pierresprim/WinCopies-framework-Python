from __future__ import annotations

from abc import abstractmethod
from collections.abc import Sized, Container, Iterable, Iterator, Collection as CollectionBase, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, SupportsIndex

from WinCopies import Collections, Abstract, IStringable
from WinCopies.Collections import Enumeration, ICountableCollection, IReadOnlyCountableList, ICountableList as ICountableListBase, IGetter, ISetter, IndexOf
from WinCopies.Collections.Abstraction.Enumeration import Enumerator
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEquatableEnumerable, IEnumerator, CountableEnumerable, GetIterator, TryAsIterator
from WinCopies.Typing import INullable, IEquatableItem, IGenericConstraint, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Delegate import Method, EqualityComparison, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Pairing import IKeyValuePair, DualValueBool
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

class IReadOnlyCollection[T](IReadOnlyCountableList[T], ICountableEnumerable[T]):
    def __init__(self):
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
    def __init__(self):
        super().__init__()

class ICollection[T](IEnumerableCollection[T], ICountableListBase[T]):
    def __init__(self):
        super().__init__()

class ISequence[T](IReadOnlyCollection[T]):
    def __init__(self):
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
    def __init__(self):
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

class ReadOnlyCollection[T](CollectionBase[T], IReadOnlyCollection[T]):
    def __init__(self):
        super().__init__()
    
    @final
    def __len__(self) -> int:
        return self.GetCount()
    
    @final
    def __contains__(self, x: object) -> bool:
        return self.Contains(x)
    
    def _TryGetIterator(self) -> Iterator[T]|None:
        return TryAsIterator(self.TryGetEnumerator())
    
    @final
    def __iter__(self) -> Iterator[T]:
        return GetIterator(self._TryGetIterator())
    
    def AsSized(self) -> Sized:
        return self
    def AsContainer(self) -> Container[T]:
        return self
    def AsIterable(self) -> Iterable[T]:
        return self
    def AsCollection(self) -> CollectionBase[T]:
        return self

class Sequence[T](SequenceBase[T], ReadOnlyCollection[T], ISequence[T]):
    def __init__(self):
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
    def __init__(self):
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
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> ITuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> ITuple[T]:
        pass
class IEquatableTuple[T: IEquatableItem](Collections.IEquatableTuple[T], ITuple[T], IEquatableEnumerable[T]):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def AsReversed(self) -> IEquatableTuple[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        pass
class IArray[T](Collections.IArray[T], ITuple[T]):
    def __init__(self):
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
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReversed(self) -> IList[T]:
        pass
    
    @abstractmethod
    def SliceAt(self, key: slice) -> IList[T]:
        pass

# TODO: Should implement a Mapping abstractor provider.
class IReadOnlyDictionary[TKey: IEquatableItem, TValue](Collections.IReadOnlyDictionary[TKey, TValue], ICountableEnumerable[IKeyValuePair[TKey, TValue]], IStringable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        pass
    @abstractmethod
    def GetValues(self) -> ICountableEnumerable[TValue]:
        pass
# TODO: Should implement a MutableMapping abstractor provider.
class IDictionary[TKey: IEquatableItem, TValue](Collections.IDictionary[TKey, TValue], IReadOnlyDictionary[TKey, TValue]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        pass

class IReadOnlySet[T: IEquatableItem](Collections.IReadOnlySet, ICountableEnumerable[T], IStringable):
    def __init__(self):
        super().__init__()
class ISet[T: IEquatableItem](Collections.ISet[T], IReadOnlySet[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def AsReadOnly(self) -> IReadOnlySet[T]:
        pass

class _Reversed[TItem, TCollection](Sequence[TItem], ITuple[TItem], GenericConstraint[TCollection, ITuple[TItem]]):
    def __init__(self, items: TCollection):
        EnsureDirectModuleCall()

        super().__init__()

        self.__items: TCollection = items
    
    @final
    def _GetIndex(self, index: int) -> int:
        return self.GetCount() - index - 1
    
    @final
    def _GetContainer(self) -> TCollection:
        return self.__items
    
    @final
    def _GetKey(self, key: slice) -> slice:
        start, stop, step = key.indices(self.GetCount())
        
        return slice(self._GetIndex(start), self._GetIndex(stop), step)
    
    @abstractmethod
    def _SliceAt(self, key: slice) -> TCollection:
        pass

    @final
    def ToSlicedAt(self, key: slice) -> TCollection:
        return self._SliceAt(self._GetKey(key))
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetInnerContainer().IsEmpty()
    
    @final
    def GetCount(self) -> int:
        return self.GetCount()
    
    @final
    def TryGetAt[TDefault](self, key: int, defaultValue: TDefault) -> DualValueBool[TItem|TDefault]:
        return self._GetInnerContainer().TryGetAt(self._GetIndex(key), defaultValue)
    
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
        return TupleBase[TItem].Enumerator(self)
    
    @final
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class _ReadOnlyTuple[T](Abstract, ITuple[T], IStringable):
    @final
    class __Reversed(_Reversed[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
        def __init__(self, items: ITuple[T]):
            super().__init__(items)
        
        def _SliceAt(self, key: slice) -> ITuple[T]:
            return self._GetContainer().SliceAt(key)
        def SliceAt(self, key: slice) -> ITuple[T]:
            return self.ToSlicedAt(key)

        def AsReversed(self) -> ITuple[T]:
            return self._GetContainer()

    @final
    class __Updater(ValueFunctionUpdater[ITuple[T]]):
        def __init__(self, array: ITuple[T], updater: Method[IFunction[ITuple[T]]]):
            super().__init__(updater)

            self.__array: ITuple[T] = array
        
        def _GetValue(self) -> ITuple[T]:
            return _ReadOnlyTuple[T].__Reversed(self.__array)
    
    def __init__(self, items: IArray[T]):
        def update(func: IFunction[ITuple[T]]) -> None:
            self.__reversed = func
        
        EnsureDirectModuleCall()

        super().__init__()

        self.__items: IArray[T] = items
        self.__reversed: IFunction[ITuple[T]] = _ReadOnlyTuple[T].__Updater(self, update)
    
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
    def TryGetAt[TDefault](self, key: int, defaultValue: TDefault) -> DualValueBool[T|TDefault]:
        return self._GetItems().TryGetAt(key, defaultValue)
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

class _ReversedArray[TItem, TCollection](_Reversed[TItem, TCollection], IArray[TItem], GenericSpecializedConstraint[TCollection, ITuple[TItem], IArray[TItem]]):
    def __init__(self, items: TCollection):
        def update(func: IFunction[ITuple[TItem]]) -> None:
            self.__readOnly = func
        
        super().__init__(items)
        
        self.__readOnly: IFunction[ITuple[TItem]] = self._GetUpdater(update)
    
    @abstractmethod
    def _GetUpdater(self, func: Method[IFunction[ITuple[TItem]]]) -> ValueFunctionUpdater[ITuple[TItem]]:
        pass
    
    def TrySetAt(self, key: int, value: TItem) -> bool:
        return self._GetSpecializedContainer().TrySetAt(self._GetIndex(key), value)
    
    def AsReadOnly(self) -> ITuple[TItem]:
        return self.__readOnly.GetValue()

class GetterBase[TKey, TValue](IGetter[TKey, TValue]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetAt(self, key: TKey) -> TValue:
        pass
    
    @final
    def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        return DualValueBool[TValue](self._GetAt(key), True) if self.ContainsKey(key) else DualValueBool[TDefault](defaultValue, False)
class SetterBase[TKey, TValue](ISetter[TKey, TValue]):
    def __init__(self):
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
    def __init__(self):
        super().__init__()

class TupleBase[T](Collections.Tuple[T], GetterBase[int, T], ITuple[T]):
    class EnumeratorBase[TItem, TList](Enumeration.EnumeratorBase[TItem], GenericConstraint[TList, ITuple[TItem]]):
        def __init__(self, items: TList):
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
    class Enumerator(EnumeratorBase[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
        def __init__(self, items: ITuple[T]):
            super().__init__(items)
    
    def __init__(self):
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
    
    # Not final to allow customization for the enumerator.
    def TryGetEnumerator(self) -> IEnumerator[T]:
        return TupleBase[T].Enumerator(self)

class Tuple[T](TupleBase[T]):
    @final
    class __Reversed(_Reversed[T, ITuple[T]], IGenericConstraintImplementation[ITuple[T]]):
        def __init__(self, items: ITuple[T]):
            super().__init__(items)
        
        def _SliceAt(self, key: slice) -> ITuple[T]:
            return self._GetContainer().SliceAt(key)
        def SliceAt(self, key: slice) -> ITuple[T]:
            return self.ToSlicedAt(key)

        def AsReversed(self) -> ITuple[T]:
            return self._GetContainer()
    
    @final
    class __Updater(ValueFunctionUpdater[ITuple[T]]):
        def __init__(self, array: Tuple[T], updater: Method[IFunction[ITuple[T]]]):
            super().__init__(updater)

            self.__array: Tuple[T] = array
        
        def _GetValue(self) -> ITuple[T]:
            return Tuple[T].__Reversed(self.__array)
    
    def __init__(self):
        def update(func: IFunction[ITuple[T]]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[ITuple[T]] = Tuple[T].__Updater(self, update)
    
    @final
    def AsReversed(self) -> ITuple[T]:
        return self.__reversed.GetValue()
class EquatableTuple[T: IEquatableItem](TupleBase[T], IEquatableTuple[T]):
    @final
    class __Reversed(_Reversed[T, IEquatableTuple[T]], IEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
        def __init__(self, items: IEquatableTuple[T]):
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
    class __Updater(ValueFunctionUpdater[IEquatableTuple[T]]):
        def __init__(self, array: EquatableTuple[T], updater: Method[IFunction[IEquatableTuple[T]]]):
            super().__init__(updater)

            self.__array: EquatableTuple[T] = array
        
        def _GetValue(self) -> IEquatableTuple[T]:
            return EquatableTuple[T].__Reversed(self.__array)
    
    def __init__(self):
        def update(func: IFunction[IEquatableTuple[T]]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__reversed: IFunction[IEquatableTuple[T]] = EquatableTuple[T].__Updater(self, update)
    
    @final
    def AsReversed(self) -> IEquatableTuple[T]:
        return self.__reversed.GetValue()

class ArrayBase[TItem, TCollection](TupleBase[TItem], KeyableBase[int, TItem], IArray[TItem]):
    class Reversed(_ReversedArray[TItem, TCollection], IArray[TItem], IGenericConstraint[TCollection, IArray[TItem]]):
        @final
        class __Updater(ValueFunctionUpdater[ITuple[TItem]]):
            def __init__(self, array: IArray[TItem], updater: Method[IFunction[ITuple[TItem]]]):
                super().__init__(updater)

                self.__array: IArray[TItem] = array
            
            def _GetValue(self) -> ITuple[TItem]:
                return _ReadOnlyTuple(self.__array)
        
        def __init__(self, items: TCollection):
            def update(func: IFunction[ITuple[TItem]]) -> None:
                self.__readOnly = func
            
            super().__init__(items)
            
            self.__readOnly: IFunction[ITuple[TItem]] = ArrayBase[TItem, TCollection].Reversed.__Updater(self, update)
        
        @final
        def _GetUpdater(self, func: Method[IFunction[ITuple[TItem]]]) -> ValueFunctionUpdater[ITuple[TItem]]:
            return ArrayBase[TItem, TCollection].Reversed.__Updater(self, func)
        
        def _SliceAt(self, key: slice) -> IArray[TItem]:
            return self._GetSpecializedContainer().SliceAt(key)
        def SliceAt(self, key: slice) -> IArray[TItem]:
            return self._AsSpecialized(self.ToSlicedAt(key))
        
        @final
        def TrySetAt(self, key: int, value: TItem) -> bool:
            return self._GetSpecializedContainer().TrySetAt(self._GetIndex(key), value)
        
        @final
        def AsReadOnly(self) -> ITuple[TItem]:
            return self.__readOnly.GetValue()

        def AsReversed(self) -> IArray[TItem]:
            return self._GetSpecializedContainer()
        
        @final
        def Move(self, x: int, y: int) -> None:
            self._GetSpecializedContainer().Move(x, y)
    
    @final
    class __ReadOnlyUpdater(ValueFunctionUpdater[ITuple[TItem]]):
        def __init__(self, array: IArray[TItem], updater: Method[IFunction[ITuple[TItem]]]):
            super().__init__(updater)

            self.__array: IArray[TItem] = array
        
        def _GetValue(self) -> ITuple[TItem]:
            return _ReadOnlyTuple[TItem](self.__array)
    
    def __init__(self):
        def updateReadOnly(func: IFunction[ITuple[TItem]]) -> None:
            self.__readOnly = func
        def updateReversed(func: IFunction[TCollection]) -> None:
            self.__reversed = func
        
        super().__init__()

        self.__readOnly: IFunction[ITuple[TItem]] = ArrayBase[TItem, TCollection].__ReadOnlyUpdater(self, updateReadOnly)
        self.__reversed: IFunction[TCollection] = self._GetUpdater(updateReversed)
    
    @abstractmethod
    def _GetUpdater(self, func: Method[IFunction[TCollection]]) -> IFunction[TCollection]:
        pass
    
    @final
    def _AsReversed(self) -> TCollection:
        return self.__reversed.GetValue()
    
    @final
    def AsReadOnly(self) -> ITuple[TItem]:
        return self.__readOnly.GetValue()

class Array[T](Collections.Array[T], ArrayBase[T, IArray[T]]):
    @final
    class __Reversed(ArrayBase[T, IArray[T]].Reversed, IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
        def __init__(self, items: IArray[T]):
            super().__init__(items)
    
    @final
    class __Updater(ValueFunctionUpdater[IArray[T]]):
        def __init__(self, array: Array[T], updater: Method[IFunction[IArray[T]]]):
            super().__init__(updater)

            self.__array: Array[T] = array
        
        def _GetValue(self) -> IArray[T]:
            return Array[T].__Reversed(self.__array)
    
    def __init__(self):
        super().__init__()
    
    @final
    def _GetUpdater(self, func: Method[IFunction[IArray[T]]]) -> IFunction[IArray[T]]:
        return Array[T].__Updater(self, func)
    
    @final
    def AsReversed(self) -> IArray[T]:
        return self._AsReversed()

class ReversedListBase[TItem, TList](ArrayBase[TItem, TList].Reversed, MutableSequence[TItem], IList[TItem]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @abstractmethod
    def _GetContainerAsList(self, container: TList) -> IList[TItem]:
        pass

    @final
    def __GetContainerAsList(self) -> IList[TItem]:
        return self._GetContainerAsList(self._GetContainer())
    
    def _SliceAt(self, key: slice) -> IList[TItem]:
        return self.__GetContainerAsList().SliceAt(key)
    def SliceAt(self, key: slice) -> IList[TItem]:
        return self._GetContainerAsList(self.ToSlicedAt(key))
    
    def Add(self, item: TItem) -> None:
        if self.GetCount() > 0:
            self.__GetContainerAsList().Insert(0, item)
        
        else:
            self.__GetContainerAsList().Add(item)
    
    def TryInsert(self, index: int, value: TItem) -> bool:
        return self.__GetContainerAsList().TryInsert(self._GetIndex(index), value)
    
    def TryRemoveAt(self, index: int) -> bool|None:
        return self.__GetContainerAsList().TryRemoveAt(self._GetIndex(index))
    
    def Clear(self) -> None:
        self.__GetContainerAsList().Clear()

    def AsReversed(self) -> IList[TItem]:
        return self.__GetContainerAsList()
    
    def AsMutableSequence(self) -> MutableSequenceBase[TItem]:
        return self
    
    def insert(self, index: int, value: TItem) -> None:
        return self.__GetContainerAsList().AsMutableSequence().insert(self._GetIndex(index), value)

    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None:
        self.__GetContainerAsList().AsMutableSequence()[self._GetIndex(int(index)) if isinstance(index, SupportsIndex) else self._GetKey(index)] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice):
        del self.__GetContainerAsList().AsMutableSequence()[self._GetIndex(index) if isinstance(index, int) else self._GetKey(index)]

class List[T](Collections.List[T], ArrayBase[T, IList[T]], IList[T]):
    @final
    class __Reversed(ReversedListBase[T, IList[T]], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
        def __init__(self, items: IList[T]):
            super().__init__(items)
        
        def _GetContainerAsList(self, container: IList[T]) -> IList[T]:
            return container
    
    @final
    class __Updater(ValueFunctionUpdater[IList[T]]):
        def __init__(self, array: List[T], updater: Method[IFunction[IList[T]]]):
            super().__init__(updater)

            self.__array: List[T] = array
        
        def _GetValue(self) -> IList[T]:
            return List[T].__Reversed(self.__array)
    
    def __init__(self):
        super().__init__()
    
    @final
    def _GetUpdater(self, func: Method[IFunction[IList[T]]]) -> IFunction[IList[T]]:
        return List[T].__Updater(self, func)
    
    @final
    def AsReversed(self) -> IList[T]:
        return self._AsReversed()

class Set[T: IEquatableItem](CountableEnumerable[T], ISet[T]):
    class _ReadOnlySet(IReadOnlySet[T]):
        def __init__(self, items: IReadOnlySet[T]):
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
    class __Updater(ValueFunctionUpdater[IReadOnlySet[T]]):
        def __init__(self, items: Set[T], updater: Method[IFunction[IReadOnlySet[T]]]):
            super().__init__(updater)

            self.__items: Set[T] = items
        
        def _GetValue(self) -> IReadOnlySet[T]:
            return self.__items._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlySet[T]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlySet[T]] = Set[T].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlySet[T]:
        return Set[T]._ReadOnlySet(self)
    @final
    def AsReadOnly(self) -> IReadOnlySet[T]:
        return self.__readOnly.GetValue()

class Dictionary[TKey: IEquatableItem, TValue](CountableEnumerable[IKeyValuePair[TKey, TValue]], IDictionary[TKey, TValue]):
    # TODO: Should inherit from Mapping
    class _ReadOnlyDictionary(IReadOnlyDictionary[TKey, TValue]):
        def __init__(self, dictionary: Dictionary[TKey, TValue]):
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
        def TryGetAt[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
            return self._GetDictionary().TryGetAt(key, defaultValue)
        
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
    class __Updater(ValueFunctionUpdater[IReadOnlyDictionary[TKey, TValue]]):
        def __init__(self, dictionary: Dictionary[TKey, TValue], updater: Method[IFunction[IReadOnlyDictionary[TKey, TValue]]]):
            super().__init__(updater)

            self.__dictionary: Dictionary[TKey, TValue] = dictionary
        
        def _GetValue(self) -> IReadOnlyDictionary[TKey, TValue]:
            return self.__dictionary._AsReadOnly()
    
    def __init__(self):
        def update(func: IFunction[IReadOnlyDictionary[TKey, TValue]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyDictionary[TKey, TValue]] = Dictionary[TKey, TValue].__Updater(self, update)
    
    def _AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        return Dictionary[TKey, TValue]._ReadOnlyDictionary(self)
    @final
    def AsReadOnly(self) -> IReadOnlyDictionary[TKey, TValue]:
        return self.__readOnly.GetValue()