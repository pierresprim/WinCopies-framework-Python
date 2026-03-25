from __future__ import annotations

from abc import abstractmethod
from bisect import bisect_left, bisect_right, insort_left, insort_right
from collections.abc import Iterable, Iterator, Sequence, MutableSequence as MutableSequenceBase, MutableMapping
from heapq import merge
from typing import overload, final, SupportsIndex

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Collections import Enumeration, Extensions, FindIndex, MakeTuple, MakeList, Move
from WinCopies.Collections.Enumeration import ICountableEnumerable, IEnumerator, CountableEnumerable, EnumeratorBase, TryAsEnumerator
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArrayBase, IArray, IList, ISortedList, ISet, IDictionary, TupleEnumerator, MutableSequence
from WinCopies.Typing import INullable, IEquatableItem, IComparableValue, SupportsRichComparison, InvalidOperationError, GetNullable, GetNullValue
from WinCopies.Typing.Decorators import Singleton, GetSingletonInstanceProvider
from WinCopies.Typing.Delegate import IFunction, IStruct, Function, EqualityComparison, Handle
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Pairing import IKeyValuePair, KeyValuePair, DualValueBool

class TupleAbstractBase[TItem, TSequence](Extensions.Sequence[TItem], Extensions.TupleAbstractBase[TItem], GenericConstraint[TSequence, Sequence[TItem]], IStringable):
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
class TupleAbstract[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Extensions.TupleAbstract[TItem]):
    def __init__(self) -> None:
        super().__init__()
class TupleBase[TItem, TSequence](TupleAbstract[TItem, TSequence], Extensions.TupleBase[TItem]):
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

class Tuple[T](TupleBase[T, Sequence[T]], Extensions.Tuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None:
        super().__init__(MakeTuple(items))
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return Tuple[T](self._GetContainer()[key])
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class EquatableTuple[T: IEquatableItem](TupleBase[T, Sequence[T]], Extensions.EquatableTuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None:
        super().__init__(MakeTuple(items))
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return EquatableTuple[T](self._GetContainer()[key])
    
    def Hash(self) -> int:
        return hash(self._GetContainer())
    
    def Equals(self, item: object) -> bool:
        return self is item
    
    def ToString(self) -> str:
        return str(self._GetContainer())

class ArrayAbstractBase[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Extensions.ArrayAbstractBase[TItem, IArrayBase[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]]):
    def __init__(self) -> None:
        super().__init__()
class ArrayAbstract[TItem, TSequence](ArrayAbstractBase[TItem, TSequence], TupleAbstract[TItem, TSequence], Extensions.ArrayAbstract[TItem, IArray[TItem]]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer()[key] = value
class ArrayBase[TItem, TSequence](TupleBase[TItem, TSequence], ArrayAbstract[TItem, TSequence], Extensions.ArrayBase[TItem, IArray[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]]):
    def __init__(self, items: TSequence) -> None:
        super().__init__(items)

class Array[T](ArrayBase[T, MutableSequenceBase[T]], Extensions.Array[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]) -> None:
        super().__init__(MakeList(items))
    
    @final
    def Move(self, x: int, y: int) -> None:
        Move(self._GetContainer(), x, y)
    
    @final
    def Swap(self, x: int, y: int) -> None:
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

class ListAbstract[T](ArrayAbstractBase[T, MutableSequenceBase[T]], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None:
        super().__init__()

        self.__items: MutableSequenceBase[T] = MakeList(items)
    
    @final
    def _GetContainer(self) -> MutableSequenceBase[T]:
        return self.__items
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0:
            return None
        
        if index >= self.GetCount():
            return False
        
        self._GetContainer().pop(index)
        
        return True
    
    @final
    def Clear(self) -> None:
        self._GetContainer().clear()
    
    def ToString(self) -> str:
        return str(self._GetContainer())
class ListBase[T](ListAbstract[T], ArrayAbstract[T, MutableSequenceBase[T]], MutableSequence[T], Extensions.List[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None:
        super().__init__(items)
    
    @final
    def Move(self, x: int, y: int) -> None:
        Move(self._GetContainer(), x, y)
    
    @final
    def Swap(self, x: int, y: int) -> None:
        super().Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]:
        return List[T](self._GetContainer()[key])
    
    @final
    def insert(self, index: int, value: T) -> None:
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
        self._GetContainer()[index] = value # type: ignore
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        del self._GetContainer()[index]
class List[T](ListBase[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None = None) -> None:
        super().__init__(items)
    
    @final
    def Add(self, item: T) -> None:
        self._GetContainer().append(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        if self.ValidateIndex(index):
            self._GetContainer().insert(index, value)
            
            return True
        
        return False

class _ISizedListInitializer[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        pass
    
    @abstractmethod
    def GetItems(self) -> MutableSequenceBase[T]|None:
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

class ISizedList[T](IList[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        pass
    
    @abstractmethod
    def ValidateLength(self) -> bool:
        pass

class SizedList[T](ListBase[T], ISizedList[T]):
    def __init__(self, initializer: _ISizedListInitializer[T]) -> None:
        super().__init__(initializer.GetItems())

        self.__maxLength: int = initializer.GetMaxLength()
    
    @final
    def GetMaxLength(self) -> int:
        return self.__maxLength
    
    @final
    def ValidateLength(self) -> bool:
        return self.GetCount() < self.GetMaxLength()
    
    @final
    def Add(self, item: T) -> None:
        if self.ValidateLength():
            self._GetContainer().append(item)
        
        else:
            raise InvalidOperationError()
    
    @final
    def TryInsertAt(self, index: int, value: T) -> bool|None:
        if self.ValidateLength():
            if self.ValidateIndex(index):
                self._GetContainer().insert(index, value)
                
                return True
            
            return False
        
        return None
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self.TryInsertAt(index, value) is True
    
    @staticmethod
    def Create(length: int) -> ISizedList[T]:
        return SizedList[T](_SizedListLengthInitializer[T](length))

def CreateSizedList[T](items: MutableSequenceBase[T]) -> ISizedList[T]:
    return SizedList[T](_SizedListSequenceInitializer[T](items))
def TryCreateSizedList[T](length: int, items: MutableSequenceBase[T]|None) -> ISizedList[T]|None:
    return SizedList[T].Create(length) if items is None else (None if length < len(items) else SizedList[T](_SizedListInitializer[T](length, items)))

class ArrayCollection[T](Extensions.Sequence[T], Extensions.ArrayCollection[T], IArray[T]):
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
    def IsEmpty(self) -> bool:
        return self._GetItems().IsEmpty()
    
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

class SortedList[T: IComparableValue|SupportsRichComparison](ListAbstract[T], Sequence[T], Extensions.SortedList[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None:
        super().__init__(None if items is None else sorted(items))
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return bisect_left(self.AsSequence(), item) if predicate is None else FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int:
        return bisect_right(self.AsSequence(), item) if predicate is None else FindIndex(self.AsReversed().AsSequence(), item, predicate)
    
    @final
    def AddLeft(self, item: T) -> None:
        return insort_left(self._GetContainer(), item)
    @final
    def Add(self, item: T) -> None:
        return insort_right(self._GetContainer(), item)
    @final
    def AddItems(self, items: Iterable[T]) -> None:
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
    
    @staticmethod
    def Create(*items: T) -> ISortedList[T]:
        return SortedList[T](items)

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
        self.__current: IKeyValuePair[TKey, TValue]|None = None
    
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
            item: tuple[TKey, TValue]|None = self.__iterator.GetCurrent()

            if item is None:
                return False

            self.__current = EnumerationKeyValuePair[TKey, TValue](item)

            return True
        
        return False
    
    def GetCurrent(self) -> IKeyValuePair[TKey, TValue]|None:
        return self.__current
    
    def _OnEnded(self) -> None:
        self.__iterator = None
        self.__current = None

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
class Dictionary[TKey: IEquatableItem, TValue](Extensions.Dictionary[TKey, TValue]):
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

class Set[T: IEquatableItem](Extensions.Set[T]):
    def __init__(self, items: set[T]|None = None) -> None:
        super().__init__()

        self.__set: set[T] = set[T]() if items is None else items
    
    @final
    def __TryAdd(self, item: T) -> int:
        count = self.GetCount()
        
        self._GetItems().add(item)
    
        return count
    
    @final
    def _GetItems(self) -> set[T]:
        return self.__set
    
    @final
    def GetCount(self) -> int:
        return len(self._GetItems())
    
    @final
    def TryAdd(self, item: T) -> bool:
        return self.__TryAdd(item) < self.GetCount()
    @final
    def Add(self, item: T) -> None:
        if self.__TryAdd(item) == self.GetCount():
            raise ValueError(f"Item {item} already exists.")
    
    @final
    def Remove(self, item: T) -> None:
        self._GetItems().remove(item)
    @final
    def TryRemove(self, item: T) -> bool:
        try:
            self.Remove(item)

            return True
        
        except KeyError:
            return False
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None:
        return TryAsEnumerator(item for item in self._GetItems())
    
    @final
    def Clear(self) -> None:
        self._GetItems().clear()
    
    def ToString(self) -> str:
        return str(self._GetItems())

def CreateTuple[T](items: Sequence[T]|Iterable[T]) -> ITuple[T]:
    return Tuple[T](items)
def CreateTupleFromValues[T](*items: T) -> ITuple[T]:
    return CreateTuple(items)

def CreateEquatableTuple[T: IEquatableItem](items: Sequence[T]|Iterable[T]) -> IEquatableTuple[T]:
    return EquatableTuple[T](items)
def CreateEquatableTupleFromValues[T: IEquatableItem](*items: T) -> IEquatableTuple[T]:
    return CreateEquatableTuple(items)

def CreateArray[T](items: MutableSequenceBase[T]|Iterable[T]) -> IArray[T]:
    return Array[T](items)
def CreateArrayFromValues[T](*items: T) -> IArray[T]:
    return CreateArray(items)

def CreateList[T](items: MutableSequenceBase[T]|Iterable[T]) -> IList[T]:
    return List[T](items)
def CreateListFromValues[T](*items: T) -> IList[T]:
    return CreateList(items)

def CreateSet[T: IEquatableItem](set: set[T]) -> ISet[T]:
    return Set[T](set)
def CreateDictionary[TKey: IEquatableItem, TValue](dictionary: MutableMapping[TKey, TValue]) -> IDictionary[TKey, TValue]:
    return Dictionary[TKey, TValue](dictionary)