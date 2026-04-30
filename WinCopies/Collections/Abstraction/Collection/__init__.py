from __future__ import annotations

from abc import abstractmethod
from bisect import bisect_left, bisect_right, insort_left, insort_right
from collections.abc import Iterable, Iterator, Sequence, MutableSequence as MutableSequenceBase, MutableMapping
from heapq import merge
from typing import overload, final, SupportsIndex

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Collections import Enumeration, Extensions, Mutability, FindIndex, MakeTuple as MakeSequence, MakeList as MakeMutableSequence, Move
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, EnumeratorBase, TryAsEnumerator
from WinCopies.Collections.Extensions import Collection, ITuple, IHashableTuple, IArrayBase, IArray, IList, ISortedList, IDictionary, MutableSequence, Count
from WinCopies.Collections.Extensions.Enumeration import TupleEnumerator
from WinCopies.Collections.Generation import IObjectMonitor
from WinCopies.Typing import INullable, IEquatableItem, SupportsRichComparison, IComparableProtocol, InvalidOperationError, GetNullable, GetNullValue
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import IFunction, IStruct, Function, Converter, EqualityComparison, Handle
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool
from WinCopies.Typing.Reflection import AreSameClass

class TupleAbstractBase[TItem, TSequence](Extensions.Sequence[TItem], Collection.TupleAbstractBase[TItem], GenericConstraint[TSequence, Sequence[TItem]], IStringable):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def GetCount(self) -> int:
        return len(self._GetInnerContainer())
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer()[key]
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return value in self._GetInnerContainer()
class TupleAbstract[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Collection.TupleAbstract[TItem]):
    def __init__(self) -> None:
        super().__init__()
class TupleBase[TItem, TSequence](TupleAbstract[TItem, TSequence], Collection.TupleBase[TItem]):
    def __init__(self, items: TSequence) -> None:
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetContainer(self) -> TSequence:
        return self.__items
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|Sequence[TItem]:
        return self._GetInnerContainer()[int(index) if isinstance(index, SupportsIndex) else index]

class Tuple[T](TupleBase[T, Sequence[T]], Collection.Tuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None:
        mutability: Mutability|None = None
        _items: Sequence[T]|None = None

        if isinstance(items, Sequence):
            _items = items
            mutability = None if AreSameClass(type(items), tuple) else Mutability.Mutable
        
        else:
            _items = list[T](items)

        super().__init__(_items)

        self.__mutability: Mutability|None = mutability
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self.__mutability
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return Tuple[T](self._GetContainer()[key])
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class EquatableTuple[T: IEquatableItem](TupleBase[T, Sequence[T]], Collection.HashableTuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None:
        super().__init__(MakeSequence(items))
    
    @final
    def TryGetSourceMutability(self) -> None:
        return None
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        return EquatableTuple[T](self._GetContainer()[key])
    
    def Hash(self) -> int:
        return hash(self._GetContainer())
    
    def Equals(self, item: object) -> bool:
        return self is item
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class ArrayAbstractBase[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Collection.ArrayAbstractBase[TItem, IArrayBase[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]]):
    def __init__(self) -> None:
        super().__init__()
class ArrayAbstract[TItem, TSequence](ArrayAbstractBase[TItem, TSequence], TupleAbstract[TItem, TSequence], Collection.ArrayAbstract[TItem, IArray[TItem]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._InvalidateEnumerators()

        self._GetSpecializedContainer()[key] = value
class ArrayBase[TItem, TSequence](TupleBase[TItem, TSequence], ArrayAbstract[TItem, TSequence], Collection.ArrayBase[TItem, IArray[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]]):
    def __init__(self, items: TSequence) -> None:
        super().__init__(items)
class Array[T](ArrayBase[T, MutableSequenceBase[T]], Collection.Array[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]) -> None:
        mutability: Mutability|None = None
        _items: MutableSequenceBase[T]|None = None

        if isinstance(items, MutableSequenceBase):
            _items = items
            mutability = Mutability.Mutable
        
        else:
            _items = list[T](items)

        super().__init__(_items)

        self.__mutability: Mutability|None = mutability
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self.__mutability
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._InvalidateEnumerators()

        Move(self._GetContainer(), x, y)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        self._InvalidateEnumerators()

        super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return Array[T](self._GetContainer()[key])
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class SizedArray[T](Array[T]):
    def __init__(self, length: int) -> None:
        super().__init__([self._GetDefaultValue()] * length)
    
    @abstractmethod
    def _GetDefaultValue(self) -> T:
        pass

class ListAbstract[T](ArrayAbstractBase[T, MutableSequenceBase[T]], Extensions.ICollection[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None:
        super().__init__()

        self.__items: MutableSequenceBase[T] = MakeMutableSequence(items)
    
    @final
    def _GetContainer(self) -> MutableSequenceBase[T]:
        return self.__items
    @abstractmethod
    def _GetEnumerationMonitor(self) -> IObjectMonitor:
        pass

    @final
    def __InvalidateEnumerators(self) -> None:
        self._GetEnumerationMonitor().InvalidateObjects()
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0:
            return None
        
        if index >= self.GetCount():
            return False
        
        self.__InvalidateEnumerators()
        
        self._GetContainer().pop(index)
        
        return True
    
    @final
    def TryRemoveRange(self, index: int, count: int) -> bool:
        if self.ValidateIndex(index):
            self.__InvalidateEnumerators()

            for i in range(count):
                self.RemoveAt(index + i)

            return True
        
        return False
    
    @final
    def Clear(self) -> None:
        self.__InvalidateEnumerators()
        
        self._GetContainer().clear()
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class ListBase[T](ListAbstract[T], ArrayAbstract[T, MutableSequenceBase[T]], MutableSequence[T], Collection.List[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None:
        super().__init__(items)
    
    @final
    def _GetEnumerationMonitor(self) -> IObjectMonitor:
        return self._GetEnumeratorFactory()
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._InvalidateEnumerators()

        Move(self._GetContainer(), x, y)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        self._InvalidateEnumerators()
        
        super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]:
        return List[T](self._GetContainer()[key])
    
    @final
    def _TryInsert(self, index: int, value: T) -> bool:
        if self.ValidateIndex(index):
            self._InvalidateEnumerators()

            self._GetContainer().insert(index, value)
            
            return True
        
        return False
    @final
    def _TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        if self.ValidateIndex(index):
            self._InvalidateEnumerators()

            index -= 1
            
            for item in items:
                index += 1

                self._GetContainer().insert(index, item)
            
            return True
        
        return False
    
    @final
    def insert(self, index: int, value: T) -> None:
        self._InvalidateEnumerators()

        self._GetContainer().insert(index, value)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]:
        return self._GetSpecializedContainer()[int(index) if isinstance(index, SupportsIndex) else index]
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
        self._InvalidateEnumerators()

        self._GetContainer()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        self._InvalidateEnumerators()

        del self._GetContainer()[index]
class List[T](ListBase[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None = None) -> None:
        super().__init__(items)
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.Mutable
    @final
    def TryGetSourceMutability(self) -> None:
        return None
    
    @final
    def Add(self, item: T) -> None:
        self._InvalidateEnumerators()

        self._GetContainer().append(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self._TryInsert(index, value)
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        return self._TryInsertRange(index, items)

class _ISizedListInitializer[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        pass
    
    @abstractmethod
    def GetItems(self) -> MutableSequenceBase[T]|None:
        pass

    @abstractmethod
    def GetMutability(self) -> Mutability|None:
        pass

class _SizedListSequenceInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, items: MutableSequenceBase[T]) -> None:
        super().__init__()

        self.__items: MutableSequenceBase[T] = items
    
    @final
    def GetItems(self) -> MutableSequenceBase[T]:
        return self.__items
    
    @final
    def GetMaxLength(self) -> int:
        return len(self.GetItems())

    @final
    def GetMutability(self) -> Mutability|None:
        return Mutability.Mutable
class _SizedListLengthInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, length: int) -> None:
        super().__init__()

        self.__length: int = length
    
    @final
    def GetItems(self) -> None:
        return None
    
    @final
    def GetMaxLength(self) -> int:
        return self.__length

    @final
    def GetMutability(self) -> Mutability|None:
        return None

class _SizedListInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, length: int, items: MutableSequenceBase[T]) -> None:
        super().__init__()

        self.__length: int = length
        self.__items: MutableSequenceBase[T] = items
    
    @final
    def GetMaxLength(self) -> int:
        return self.__length
    
    @final
    def GetItems(self) -> MutableSequenceBase[T]:
        return self.__items

    @final
    def GetMutability(self) -> Mutability|None:
        return Mutability.Mutable

class ISizedList[T](IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        pass
    
    @abstractmethod
    def ValidateLength(self, count: int) -> bool:
        pass
    
    @abstractmethod
    def TryInsertAt(self, index: int, value: T) -> bool|None:
        pass
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self.TryInsertAt(index, value) is True
    
    @abstractmethod
    def TryInsertRangeAt(self, index: int, items: Iterable[T]) -> bool|None:
        pass
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool:
        return self.TryInsertRangeAt(index, items) is True

class SizedList[T](ListBase[T], ISizedList[T]):
    def __init__(self, initializer: _ISizedListInitializer[T]) -> None:
        super().__init__(initializer.GetItems())

        self.__maxLength: int = initializer.GetMaxLength()
        self.__mutability: Mutability|None = initializer.GetMutability()
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self.__mutability
    
    @final
    def GetMaxLength(self) -> int:
        return self.__maxLength
    
    @final
    def ValidateLength(self, count: int) -> bool:
        return self.GetCount() + count <= self.GetMaxLength()
    
    @final
    def Add(self, item: T) -> None:
        if self.ValidateLength(1):
            self._InvalidateEnumerators()

            self._GetContainer().append(item)
        
        else:
            raise InvalidOperationError()
    
    @final
    def TryInsertAt(self, index: int, value: T) -> bool|None:
        return self._TryInsert(index, value) if self.ValidateLength(1) else None
    @final
    def TryInsertRangeAt(self, index: int, items: Iterable[T]) -> bool|None:
        _items: tuple[Iterable[T], int] = Count(items)
        
        return self._TryInsertRange(index, _items[0]) if self.ValidateLength(_items[1]) else None
    
    @staticmethod
    def Create(length: int) -> ISizedList[T]:
        return SizedList[T](_SizedListLengthInitializer[T](length))

class ArrayCollection[T](Extensions.Sequence[T], Collection.ArrayCollection[T], IArray[T]):
    def __init__(self, array: IArray[IStruct[T]]) -> None:
        super().__init__()

        self.__array: IArray[IStruct[T]] = array
    
    @final
    def _GetItems(self) -> IArray[IStruct[T]]:
        return self.__array
    
    @final
    def _GetStructAt(self, index: int) -> IStruct[T]:
        return self._GetItems().GetAt(index)

    @final
    def _GetAt(self, key: int) -> T:
        return self._GetStructAt(key).GetValue()
    @final
    def _SetAt(self, key: int, value: T) -> None:
        self._GetStructAt(key).SetValue(value)
    
    @final
    def GetMutability(self) -> Mutability:
        return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self._GetItems().TryGetSourceMutability()
    
    @final
    def GetCount(self) -> int:
        return self._GetItems().GetCount()
    
    @final
    def Contains(self, value: T|object) -> bool:
        return value in self.AsSequence()
    
    @final
    def Move(self, x: int, y: int) -> None:
        self._GetItems().Move(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return ArrayCollection[T](self._GetItems().SliceAt(key))
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TupleEnumerator[T](self)
    
    @final
    def ToString(self) -> str:
        return self._GetItems().ToString()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]:
        return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class ArrayList[T](ArrayCollection[T]):
    def __init__(self, length: int, func: IFunction[T]) -> None:
        super().__init__(Array[IStruct[T]]((Handle[T](func) for _ in range(length))))

class SortedList[T: IComparableProtocol](ListAbstract[T], Sequence[T], Collection.SortedList[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        super().__init__(None if items is None else sorted(items))
    
    @final
    def _GetEnumerationMonitor(self) -> IObjectMonitor:
        return self._GetEnumeratorFactory()
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return bisect_left(self.AsSequence(), item) if predicate is None else FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return bisect_right(self.AsSequence(), item) if predicate is None else FindIndex(self.AsReversed().AsSequence(), item, predicate)
    
    @final
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int:
        return bisect_left(self.AsSequence(), item, key = converter)
    @final
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int:
        return bisect_right(self.AsSequence(), item, key = converter)
    
    @final
    def AddLeft(self, item: T) -> None:
        return insort_left(self._GetContainer(), item)
    @final
    def Add(self, item: T) -> None:
        return insort_right(self._GetContainer(), item)
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        self._GetContainer()[:] = merge(self.AsSequence(), sorted(items))
    
    @final
    def SliceAt(self, key: slice) -> ISortedList[T]:
        return SortedList[T](self._GetContainer()[key])
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]:
        return self._GetInnerContainer()[int(index) if isinstance(index, SupportsIndex) else index]

@final
class EnumerationKeyValuePair[TKey: IEquatableItem, TValue](Abstract, IKeyValuePair[TKey, TValue]):
    def __init__(self, item: tuple[TKey, TValue]) -> None:
        super().__init__()
        
        self.__item: tuple[TKey, TValue] = item
    
    @final
    def IsKeyValuePair(self) -> bool:
        return True
    
    @final
    def GetKey(self) -> TKey:
        return self.__item[0]
    @final
    def GetValue(self) -> TValue:
        return self.__item[1]

    @final
    def _Equals(self, item: IKeyValuePair[TKey, TValue]|object) -> bool:
        return isinstance(item, EnumerationKeyValuePair)

@final
class DictionaryEnumerator[TKey: IEquatableItem, TValue](EnumeratorBase[IKeyValuePair[TKey, TValue]]):
    def __init__(self, dictionary: MutableMapping[TKey, TValue]) -> None:
        super().__init__()

        self.__dictionary: MutableMapping[TKey, TValue] = dictionary
        self.__iterator: Enumeration.Iterator[tuple[TKey, TValue]]|None = None
        self.__current: INullable[IKeyValuePair[TKey, TValue]] = GetNullValue()
    
    def IsResetSupported(self) -> bool:
        return True
    
    def _OnStarting(self) -> bool:
        if super()._OnStarting():
            self.__iterator = Enumeration.Iterator(self.__dictionary.items().__iter__())
            
            return True
        
        return False
    
    def _MoveNextOverride(self) -> bool:
        if self.__iterator is None:
            return False
        
        if self.__iterator.MoveNext():
            self.__current = GetNullable(EnumerationKeyValuePair[TKey, TValue](self.__iterator.GetCurrent()))

            return True
        
        return False
    
    def _GetCurrent(self) -> IKeyValuePair[TKey, TValue]:
        return self.__current.GetValue()
    
    def _OnEnded(self) -> None:
        self.__iterator = None
        self.__current = GetNullValue()

        super()._OnEnded()
    
    def _OnStopped(self) -> None:
        pass
    
    def _ResetOverride(self) -> bool:
        return True

@final
class _None(Singleton):
    def __init__(self) -> None:
        super().__init__()

# TODO: Should inherit from MutableMapping
class Dictionary[TKey: IEquatableItem, TValue](Collection.Dictionary[TKey, TValue]):
    class _Enumerable[_TKey: IEquatableItem, _TValue, _TItem](CountableEnumerable[_TItem]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None:
            super().__init__()

            self.__dic: Dictionary[_TKey, _TValue] = dic
        
        @final
        def _GetDictionary(self) -> MutableMapping[_TKey, _TValue]:
            return self.__dic._GetDictionary()
        
        @final
        def GetCount(self) -> int:
            return self.__dic.GetCount()
        
        @final
        def TryGetEnumerator(self) -> IEnumerator[_TItem]|None:
            return TryAsEnumerator(self._TryGetIterator())
    @final
    class _KeyEnumerable[_TKey: IEquatableItem, _TValue](_Enumerable[_TKey, _TValue, _TKey]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None:
            super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[_TKey]|None:
            return iter(self._GetDictionary().keys())
    @final
    class _ValueEnumerable[_TKey: IEquatableItem, _TValue](_Enumerable[_TKey, _TValue, _TValue]):
        def __init__(self, dic: Dictionary[_TKey, _TValue]) -> None:
            super().__init__(dic)
        
        def _TryGetIterator(self) -> Iterator[_TValue]|None:
            return iter(self._GetDictionary().values())
    
    __getInstance: Function[_None] = GetSingletonInstanceProvider(_None)
    
    @staticmethod
    def __GetNoneInstance() -> _None:
        return Dictionary[TKey, TValue].__getInstance() # pyright: ignore[reportUnknownMemberType,reportUnknownVariableType,reportAttributeAccessIssue]
    
    def __init__(self, dictionary: MutableMapping[TKey, TValue]|None = None) -> None:
        super().__init__()

        self.__dictionary: MutableMapping[TKey, TValue] = dict[TKey, TValue]() if dictionary is None else dictionary
        self.__keys: ICountableEnumerable[TKey] = Dictionary._KeyEnumerable(self)
        self.__values: ICountableEnumerable[TValue] = Dictionary._ValueEnumerable(self)
    
    @final
    def __TryAdd(self, key: TKey, value: TValue) -> int:
        count = self.GetCount()
        
        self._GetDictionary().setdefault(key, value)
    
        return count
    
    @final
    def __SetAt(self, key: TKey, value: TValue) -> None:
        self._GetDictionary()[key] = value
    
    @final
    def _GetDictionary(self) -> MutableMapping[TKey, TValue]:
        return self.__dictionary
    
    @final
    def GetCount(self) -> int:
        return len(self._GetDictionary())
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return key in self._GetDictionary()
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TValue]:
        result: TValue|_None = self._GetDictionary().get(key, Dictionary[TKey, TValue].__getInstance()) # pyright: ignore[reportUnknownMemberType,reportUnknownArgumentType,reportAttributeAccessIssue]

        return GetNullValue() if isinstance(result, _None) else GetNullable(result)
    
    @final
    def TrySetAt(self, key: TKey, value: TValue) -> bool:
        if key in self.GetKeys().AsIterable():
            self.__SetAt(key, value)

            return True
        
        return False
    
    @final
    def GetKeys(self) -> ICountableEnumerable[TKey]:
        return self.__keys
    @final
    def GetValues(self) -> ICountableEnumerable[TValue]:
        return self.__values
    
    @final
    def TryAdd(self, key: TKey, value: TValue) -> bool:
        return self.__TryAdd(key, value) < self.GetCount()
    @final
    def TryAddItem(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.TryAdd(item.GetKey(), item.GetValue())
    
    @final
    def Add(self, key: TKey, value: TValue) -> None:
        if self.__TryAdd(key, value) == self.GetCount():
            raise KeyError(f"Key {key} already exists.")
    @final
    def AddItem(self, item: KeyValuePair[TKey, TValue]) -> None:
        self.Add(item.GetKey(), item.GetValue())
    
    @final
    def AddOrUpdate(self, key: TKey, value: TValue) -> bool:
        if self.TryAdd(key, value):
            return True
        
        self.__SetAt(key, value)

        return False
    @final
    def AddItemOrUpdate(self, item: KeyValuePair[TKey, TValue]) -> bool:
        return self.AddOrUpdate(item.GetKey(), item.GetValue())

    @final
    def Remove(self, key: TKey) -> None:
        self._GetDictionary().pop(key)
    
    @final
    def TryRemove[TDefault](self, key: TKey, defaultValue: TDefault) -> DualValueBool[TValue|TDefault]:
        def getResult(key: TValue|TDefault, value: bool) -> DualValueBool[TValue|TDefault]:
            return DualValueBool[TValue|TDefault](key, value)
        
        result: TValue|_None = self._GetDictionary().pop(key, Dictionary.__GetNoneInstance())

        return getResult(defaultValue, False) if isinstance(result, _None) else getResult(result, True)
    
    @final
    def Clear(self) -> None:
        self._GetDictionary().clear()
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[IKeyValuePair[TKey, TValue]]:
        return DictionaryEnumerator[TKey, TValue](self._GetDictionary())
    
    def ToString(self) -> str:
        return str(self._GetDictionary())

def CreateTuple[T](items: Sequence[T]|Iterable[T]) -> ITuple[T]:
    return Tuple[T](items)
def MakeTuple[T](*items: T) -> ITuple[T]:
    return CreateTuple(items)

def CreateEquatableTuple[T: IEquatableItem](items: Sequence[T]|Iterable[T]) -> IHashableTuple[T]:
    return EquatableTuple[T](items)
def MakeEquatableTuple[T: IEquatableItem](*items: T) -> IHashableTuple[T]:
    return CreateEquatableTuple(items)

def CreateArray[T](items: MutableSequenceBase[T]|Iterable[T]) -> IArray[T]:
    return Array[T](items)
def MakeArray[T](*items: T) -> IArray[T]:
    return CreateArray(items)

def CreateList[T](items: MutableSequenceBase[T]|Iterable[T]) -> IList[T]:
    return List[T](items)
def MakeList[T](*items: T) -> IList[T]:
    return CreateList(items)

def CreateSizedList[T](items: MutableSequenceBase[T]) -> ISizedList[T]:
    return SizedList[T](_SizedListSequenceInitializer[T](items))
def TryCreateSizedList[T](length: int, items: MutableSequenceBase[T]|None) -> ISizedList[T]|None:
    return SizedList[T].Create(length) if items is None else (None if length < len(items) else SizedList[T](_SizedListInitializer[T](length, items)))

def CreateArrayList[T](length: int, func: IFunction[T]) -> IArray[T]:
    return ArrayList[T](length, func)

def CreateSortedList[T: IComparableProtocol](items: Iterable[T]) -> ISortedList[T]:
    return SortedList[T](items)
def MakeSortedList[T: IComparableProtocol](*items: T) -> ISortedList[T]:
    return CreateSortedList(items)

def CreateDictionary[TKey: IEquatableItem, TValue](dictionary: MutableMapping[TKey, TValue]) -> IDictionary[TKey, TValue]:
    return Dictionary[TKey, TValue](dictionary)