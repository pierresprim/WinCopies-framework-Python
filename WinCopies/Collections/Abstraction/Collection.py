from __future__ import annotations

from abc import abstractmethod
from bisect import bisect_left, bisect_right, insort_left, insort_right
from collections.abc import Iterable, Sequence, MutableSequence as MutableSequenceBase
from heapq import merge
from typing import overload, final, Callable, SupportsIndex

from WinCopies import IInterface, IStringable, Abstract, IsTrue
from WinCopies.Collections import Extensions
from WinCopies.Collections.Core import Mutability, IEquatableTuple as IEquatableTupleBase
from WinCopies.Collections.Enumeration import IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import Collection, ITuple, IEquatableTuple, IHashableTuple, IArray, IList, ISortedList, MutableSequence, Count
from WinCopies.Collections.Extensions.Collection import IViewProvider
from WinCopies.Collections.Generation.Factory import IObjectMonitor
from WinCopies.Collections.Iteration import Zip
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Collections.Loop import IterateFromAllItems, ForEachItem
from WinCopies.Collections.Util import FindIndex, CreateTuple as CreateImmutableSequence, CreateList as CreateMutableSequence, Move
from WinCopies.Typing import InvalidOperationError
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import IFunction, IStruct, Method, Converter, EqualityComparison, Handle
from WinCopies.Typing.Generic import IContainer, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Protocols import SupportsRichComparison
from WinCopies.Typing.Reflection import AreSameClass

class TupleAbstractBase[TItem, TSequence](Extensions.Sequence[TItem], Collection.TupleAbstractBase[TItem], GenericConstraint[TSequence, Sequence[TItem]], IStringable):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetCount(self) -> int: return len(self._GetInnerContainer())
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer()[key]
    
    @final
    def Contains(self, value: TItem|object) -> bool: return value in self._GetInnerContainer()
class TupleAbstract[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Collection.TupleAbstract[TItem]):
    def __init__(self) -> None: super().__init__()
class TupleBase[TItem, TSequence](TupleAbstract[TItem, TSequence], Collection.TupleBase[TItem]):
    def __init__(self, items: TSequence) -> None:
        super().__init__()

        self.__items: TSequence = items
    
    @final
    def _GetContainer(self) -> TSequence: return self.__items
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|Sequence[TItem]: return self._GetInnerContainer()[int(index) if isinstance(index, SupportsIndex) else index]

class _IEquatableTuple[T: EquatableProtocol](IEquatableTuple[T], IContainer[Sequence[T]]):
    def __init__(self) -> None: super().__init__()
    
    def Equals(self, item: object) -> bool:
        if self is item: return True
        
        match item:
            case _IEquatableTuple(): return self._GetContainer() == item._GetContainer()
            case IEquatableTuple(): return self.GetCount() == item.GetCount() and IsTrue(ForEachItem(Zip(self, item), lambda item: item.GetKey() == item.GetValue()))
            case IEquatableTupleBase(): return item.Equals(self)
            
            case _: return False

class Tuple[T](TupleBase[T, Sequence[T]], Collection.Tuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None:
        mutability: Mutability|None = None
        _items: Sequence[T]|None = None

        if isinstance(items, Sequence):
            _items = items
            mutability = None if AreSameClass(type(items), tuple) else Mutability.Mutable
        
        else: _items = list[T](items)

        super().__init__(_items)

        self.__mutability: Mutability|None = mutability
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__mutability
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return Tuple[T](self._GetContainer()[key])
    
    def ToString(self) -> str: return str(self._GetContainer())
class EquatableTuple[T: EquatableProtocol](TupleBase[T, Sequence[T]], Collection.EquatableTuple[T], _IEquatableTuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None: super().__init__(CreateImmutableSequence(items))
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    @final
    def TryGetSourceMutability(self) -> None: return None
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return EquatableTuple[T](self._GetContainer()[key])
    
    def ToString(self) -> str: return str(self._GetContainer())
class HashableTuple[T: HashableProtocol](TupleBase[T, Sequence[T]], Collection.HashableTuple[T], _IEquatableTuple[T], IGenericConstraintImplementation[Sequence[T]]):
    def __init__(self, items: Sequence[T]|Iterable[T]) -> None: super().__init__(CreateImmutableSequence(items))
    
    @final
    def TryGetSourceMutability(self) -> None: return None
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]: return HashableTuple[T](self._GetContainer()[key])
    
    def Hash(self) -> int: return hash(self._GetContainer())
    
    def ToString(self) -> str: return str(self._GetContainer())

class ArrayAbstractBase[TItem, TSequence](TupleAbstractBase[TItem, TSequence], Collection.ArrayAbstractBase[TItem, ITuple[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]], IViewProvider):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Move(self, x: int, y: int) -> None:
        self._InvalidateViews()

        Move(self._GetSpecializedContainer(), x, y)
class ArrayAbstract[TItem, TSequence](ArrayAbstractBase[TItem, TSequence], TupleAbstract[TItem, TSequence], Collection.ArrayAbstract[TItem, IArray[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._InvalidateViews()

        self._GetSpecializedContainer()[key] = value
class ArrayBase[TItem, TSequence](TupleBase[TItem, TSequence], ArrayAbstract[TItem, TSequence], Collection.ArrayBase[TItem, IArray[TItem]], GenericSpecializedConstraint[TSequence, Sequence[TItem], MutableSequenceBase[TItem]]):
    def __init__(self, items: TSequence) -> None: super().__init__(items)
class Array[T](ArrayBase[T, MutableSequenceBase[T]], Collection.Array[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]) -> None:
        mutability: Mutability|None = None
        _items: MutableSequenceBase[T]|None = None

        if isinstance(items, MutableSequenceBase):
            _items = items
            mutability = Mutability.Mutable
        
        else: _items = list[T](items)

        super().__init__(_items)

        self.__mutability: Mutability|None = mutability
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__mutability
    
    @final
    def _Swap(self, x: int, y: int) -> None:
        self._InvalidateViews()

        super()._Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return Array[T](self._GetContainer()[key])
    
    def ToString(self) -> str: return str(self._GetContainer())
class SizedArray[T](Array[T]):
    def __init__(self, length: int, defaultValue: T) -> None: super().__init__([defaultValue] * length)

class ListAbstract[T](ArrayAbstractBase[T, MutableSequenceBase[T]], Extensions.ICollection[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None:
        super().__init__()

        self.__items: MutableSequenceBase[T] = CreateMutableSequence(items)
    
    @final
    def _GetContainer(self) -> MutableSequenceBase[T]: return self.__items
    @abstractmethod
    def _GetCollectionMonitors(self) -> IObjectMonitor:
        ...

    @final
    def __InvalidateViews(self) -> None:
        self._GetCollectionMonitors().InvalidateObjects()
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        if index < 0: return None
        if index >= self.GetCount(): return False
        
        self.__InvalidateViews()
        
        self._GetContainer().pop(index)
        
        return True
    
    @final
    def Clear(self) -> None:
        if self.GetCount() > 0:
            self.__InvalidateViews()
            
            self._GetContainer().clear()
    
    def ToString(self) -> str: return str(self._GetContainer())
class ListBase[T](ListAbstract[T], ArrayAbstract[T, MutableSequenceBase[T]], MutableSequence[T], Collection.List[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None) -> None: super().__init__(items)
    
    @final
    def _GetCollectionMonitors(self) -> IObjectMonitor: return self._GetCollectionFactories()
    
    @final
    def _Swap(self, x: int, y: int) -> None:
        self._InvalidateViews()
        
        super()._Swap(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]: return List[T](self._GetContainer()[key])

    @final
    def __Insert[U](self, index: int, value: U, add: Converter[MutableSequenceBase[T], Method[U]], insert: Converter[MutableSequenceBase[T], Callable[[int, U], None]]) -> None:
        items: MutableSequenceBase[T] = self._GetContainer()

        if index == self.GetCount(): add(items)(value)
        else: insert(items)(index, value)
    
    @final
    def _TryInsert(self, index: int, value: T) -> bool:
        if self.ValidateIndex(index, True):
            self._InvalidateViews()

            self.__Insert(index, value, lambda items: items.append, lambda items: items.insert)

            return True

        return False
    @final
    def _TryInsertRange(self, index: int, items: Iterable[T]) -> bool|None:
        def extendAt(items: MutableSequenceBase[T], index: int, values: Iterable[T]) -> None: items[index:index] = values

        return IterateFromAllItems(items, lambda items: self.__Insert(index, items, lambda items: items.extend, lambda items: lambda index, values: extendAt(items, index, values)), self._InvalidateViews) if  self.ValidateIndex(index, True) else None
    @final
    def _RemoveRange(self, index: int, count: int) -> None:
        self._InvalidateViews()

        del self._GetContainer()[index:index + count]
    
    @final
    def insert(self, index: int, value: T) -> None: self.Insert(index, value)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|MutableSequenceBase[T]: return GetItems(self, index)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None: SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice) -> None: RemoveItems(self, index)
class List[T](ListBase[T]):
    def __init__(self, items: MutableSequenceBase[T]|Iterable[T]|None = None) -> None: super().__init__(items)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    @final
    def TryGetSourceMutability(self) -> None: return None
    
    @final
    def Add(self, item: T) -> None:
        self._InvalidateViews()
        
        self._GetContainer().append(item)
    @final
    def AddRange(self, items: Iterable[T]) -> None: IterateFromAllItems(items, self._GetContainer().extend, self._InvalidateViews)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool: return self._TryInsert(index, value)
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool|None: return self._TryInsertRange(index, items)

class _ISizedListInitializer[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        ...
    
    @abstractmethod
    def GetItems(self) -> MutableSequenceBase[T]|None:
        ...

    @abstractmethod
    def GetMutability(self) -> Mutability|None:
        ...

class _SizedListSequenceInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, items: MutableSequenceBase[T]) -> None:
        super().__init__()

        self.__items: MutableSequenceBase[T] = items
    
    @final
    def GetItems(self) -> MutableSequenceBase[T]: return self.__items
    
    @final
    def GetMaxLength(self) -> int: return len(self.GetItems())

    @final
    def GetMutability(self) -> Mutability|None: return Mutability.Mutable
class _SizedListLengthInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, length: int) -> None:
        super().__init__()

        self.__length: int = length
    
    @final
    def GetItems(self) -> None: return None
    
    @final
    def GetMaxLength(self) -> int: return self.__length

    @final
    def GetMutability(self) -> Mutability|None: return None

class _SizedListInitializer[T](Abstract, _ISizedListInitializer[T]):
    def __init__(self, length: int, items: MutableSequenceBase[T]) -> None:
        super().__init__()

        self.__length: int = length
        self.__items: MutableSequenceBase[T] = items
    
    @final
    def GetMaxLength(self) -> int: return self.__length
    
    @final
    def GetItems(self) -> MutableSequenceBase[T]: return self.__items

    @final
    def GetMutability(self) -> Mutability|None: return Mutability.Mutable

class ISizedList[T](IList[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetMaxLength(self) -> int:
        ...
    
    @abstractmethod
    def ValidateLength(self, count: int) -> bool:
        ...
    
    @abstractmethod
    def TryInsertAt(self, index: int, value: T) -> bool|None:
        ...
    @final
    def TryInsert(self, index: int, value: T) -> bool: return self.TryInsertAt(index, value) is True

class SizedList[T](ListBase[T], ISizedList[T]):
    def __init__(self, initializer: _ISizedListInitializer[T]) -> None:
        super().__init__(initializer.GetItems())

        self.__maxLength: int = initializer.GetMaxLength()
        self.__mutability: Mutability|None = initializer.GetMutability()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self.__mutability
    
    @final
    def GetMaxLength(self) -> int: return self.__maxLength
    
    @final
    def ValidateLength(self, count: int) -> bool: return self.GetCount() + count <= self.GetMaxLength()

    @final
    def __Add[U](self, count: int, items: U, adder: Method[U]) -> None:
        if self.ValidateLength(count):
            self._InvalidateViews()

            adder(items)
        
        else: raise InvalidOperationError("The list is already full.")
    
    @final
    def Add(self, item: T) -> None:
        self.__Add(1, item, self._GetContainer().append)
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        _items: tuple[Iterable[T], int] = Count(items)
        count: int = _items[1]

        if count > 0: self.__Add(count, _items[0], self._GetContainer().extend)
    
    @final
    def TryInsertAt(self, index: int, value: T) -> bool|None: return self._TryInsert(index, value) if self.ValidateLength(1) else None
    @final
    def TryInsertRange(self, index: int, items: Iterable[T]) -> bool|None:
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
        self._InvalidateViews()

        self._GetStructAt(key).SetValue(value)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetItems().TryGetSourceMutability()
    
    @final
    def GetCount(self) -> int: return self._GetItems().GetCount()
    
    @final
    def Contains(self, value: T|object) -> bool: return value in self.AsSequence()
    
    @final
    def _Move(self, x: int, y: int) -> None:
        self._InvalidateViews()
        
        self._GetItems().Move(x, y)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return ArrayCollection[T](self._GetItems().SliceAt(key))
    
    @final
    def TryGetEnumerator(self) -> IEnumerator[T]|None: return self.__array.GetCollectionMonitors().GetEnumeratorMonitor().CreateEnumerator(self)
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[T]|None: return self.__array.GetCollectionMonitors().GetEnumeratorMonitor().CreateResumableEnumerator(self)

    @final
    def AsImmutable(self) -> ITuple[T]: return self._GetCollectionViewMonitor().GetImmutableView()
    
    @final
    def ToString(self) -> str: return self._GetItems().ToString()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]: return self.GetAt(int(index)) if isinstance(index, SupportsIndex) else self.SliceAt(index).AsSequence()

class ArrayList[T](ArrayCollection[T]):
    def __init__(self, length: int, func: IFunction[T]) -> None: super().__init__(Array[IStruct[T]]((Handle[T](func) for _ in range(length))))

class SortedList[T: SupportsRichComparison](ListAbstract[T], Sequence[T], Collection.SortedList[T], IGenericSpecializedConstraintImplementation[Sequence[T], MutableSequenceBase[T]]):
    def __init__(self, items: Iterable[T]|None = None) -> None: super().__init__(None if items is None else sorted(items))
    
    @final
    def _GetCollectionMonitors(self) -> IObjectMonitor: return self._GetCollectionFactories()
    
    @final
    def FindFirstIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return bisect_left(self.AsSequence(), item) if predicate is None else FindIndex(self.AsSequence(), item, predicate)
    @final
    def FindLastIndex(self, item: T, predicate: EqualityComparison[T]|None = None) -> int: return bisect_right(self.AsSequence(), item) if predicate is None else FindIndex(self.AsReversed().AsSequence(), item, predicate)
    
    @final
    def BisectLeft[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return bisect_left(self.AsSequence(), item, key = converter)
    @final
    def BisectRight[_T: SupportsRichComparison](self, item: _T, converter: Converter[T, _T]) -> int: return bisect_right(self.AsSequence(), item, key = converter)

    @final
    def __Add(self, item: T, adder: Callable[[MutableSequenceBase[T], T], None]) -> None:
        self._InvalidateViews()

        adder(self._GetContainer(), item)
    
    @final
    def AddLeft(self, item: T) -> None: self.__Add(item, insort_left)
    @final
    def Add(self, item: T) -> None: self.__Add(item, insort_right)
    @final
    def AddRange(self, items: Iterable[T]) -> None:
        def _merge(items: Iterable[T]) -> None: self._GetContainer()[:] = merge(self.AsSequence(), sorted(items))
        
        IterateFromAllItems(items, _merge, self._InvalidateViews)
    
    @final
    def SliceAt(self, key: slice) -> ISortedList[T]: return SortedList[T](self._GetContainer()[key])
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Sequence[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|Sequence[T]: return self._GetInnerContainer()[int(index) if isinstance(index, SupportsIndex) else index]

def CreateTuple[T](items: Sequence[T]|Iterable[T]) -> ITuple[T]:
    return Tuple[T](items)
def MakeTuple[T](*items: T) -> ITuple[T]:
    return CreateTuple(items)

def CreateEquatableTuple[T: EquatableProtocol](items: Sequence[T]|Iterable[T]) -> IEquatableTuple[T]:
    return EquatableTuple[T](items)
def MakeEquatableTuple[T: EquatableProtocol](*items: T) -> IEquatableTuple[T]:
    return CreateEquatableTuple(items)

def CreateHashableTuple[T: HashableProtocol](items: Sequence[T]|Iterable[T]) -> IHashableTuple[T]:
    return HashableTuple[T](items)
def MakeHashableTuple[T: HashableProtocol](*items: T) -> IHashableTuple[T]:
    return CreateHashableTuple(items)

def CreateArray[T](items: MutableSequenceBase[T]|Iterable[T]) -> IArray[T]:
    return Array[T](items)
def MakeArray[T](*items: T) -> IArray[T]:
    return CreateArray(items)

def CreateList[T](items: MutableSequenceBase[T]|Iterable[T]|None = None) -> IList[T]:
    return List[T](items)
def MakeList[T](*items: T) -> IList[T]:
    return CreateList(items)

def CreateSizedList[T](items: MutableSequenceBase[T]) -> ISizedList[T]:
    return SizedList[T](_SizedListSequenceInitializer[T](items))
def TryCreateSizedList[T](length: int, items: MutableSequenceBase[T]|None) -> ISizedList[T]|None:
    return SizedList[T].Create(length) if items is None else (None if length < len(items) else SizedList[T](_SizedListInitializer[T](length, items)))

def CreateArrayList[T](length: int, func: IFunction[T]) -> IArray[T]:
    return ArrayList[T](length, func)

def CreateSortedList[T: SupportsRichComparison](items: Iterable[T]) -> ISortedList[T]:
    return SortedList[T](items)
def MakeSortedList[T: SupportsRichComparison](*items: T) -> ISortedList[T]:
    return CreateSortedList(items)



def GetTuple[T](items: ITuple[T]|Sequence[T]|Iterable[T]) -> ITuple[T]:
    return items if isinstance(items, ITuple) else CreateTuple(items)
def GetEquatableTuple[T: EquatableProtocol](items: IEquatableTuple[T]|Sequence[T]|Iterable[T]) -> IEquatableTuple[T]:
    return items if isinstance(items, IEquatableTuple) else CreateEquatableTuple(items)
def GetHashableTuple[T: HashableProtocol](items: IHashableTuple[T]|Sequence[T]|Iterable[T]) -> IHashableTuple[T]:
    return items if isinstance(items, IHashableTuple) else CreateHashableTuple(items)

def GetArray[T](items: IArray[T]|MutableSequenceBase[T]|Iterable[T]) -> IArray[T]:
    return items if isinstance(items, IArray) else CreateArray(items)

def GetList[T](items: IList[T]|MutableSequenceBase[T]|Iterable[T]|None = None) -> IList[T]:
    return items if isinstance(items, IList) else CreateList(items)
def GetSizedList[T](items: ISizedList[T]|MutableSequenceBase[T]) -> ISizedList[T]:
    return items if isinstance(items, ISizedList) else CreateSizedList(items)
def GetSortedList[T: SupportsRichComparison](items: ISortedList[T]|Iterable[T]) -> ISortedList[T]:
    return items if isinstance(items, ISortedList) else CreateSortedList(items)