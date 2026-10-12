from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import final, overload, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IHashableTuple, IArray, IList, Sequence, MutableSequence
from WinCopies.Collections.Extensions.Collection import IManagedCollection, TupleAbstract, TupleBase, ArrayBase, Tuple, EquatableTuple, HashableTuple, Array, List
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.IO.Stream import IMemoryTextStream, MemoryTextStream
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import Method, Converter, IndexedValueAction, IndexedValueFunction
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
from WinCopies.Typing.Object import Finalizer

class ICircularTuple[T](ITuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetStart(self) -> int:
        ...
    
    @final
    def TryGetCircularIndex(self, index: int, permissive: bool = False) -> int|None:
        return (self.GetIndex(index, self.GetStart())[0] if index < self.GetCount() else -1) if self.ValidateIndex(index, permissive) else None
    @final
    def GetCircularIndex(self, index: int, permissive: bool = False) -> int:
        result: int|None = self.TryGetCircularIndex(index, permissive)

        if result is None: raise IndexError(index)

        return result
class ICircularEquatableTuple[T: EquatableProtocol](ICircularTuple[T], IEquatableTuple[T]):
    def __init__(self) -> None: super().__init__()
class ICircularHashableTuple[T: HashableProtocol](ICircularTuple[T], IHashableTuple[T]):
    def __init__(self) -> None: super().__init__()
class ICircularArray[T](IArray[T], ICircularTuple[T]):
    def __init__(self) -> None: super().__init__()
class ICircularList[T](IList[T], ICircularArray[T]):
    def __init__(self) -> None: super().__init__()

class CircularAbstract[TItem, TList](TupleAbstract[TItem], ICircularTuple[TItem], IManagedCollection[TItem], IStringable, GenericConstraint[TList, ITuple[TItem]]):
    """
    Reads a container from a start and wraps around: over (2, 0, 1) with start 1, it reads
    (0, 1, 2).

    The start is a physical position in the container. A change of the container made through
    another path, directly or through another of its views, leaves the start where it is, and what
    this object reads rotates with the container.

    Such a change can leave the start past the count, so the start is reduced modulo the count
    wherever it is used, GetStart included, and is 0 for an empty container. A read never stores
    the reduced value back: a container that shrinks and grows again by another path can bring
    back a start that was reduced in between.

    A circular list's own insertions and removals are expressed in logical indices and move the
    start to honour the IList contract: an item inserted at index 0 becomes the head, an appended
    item becomes the last one, and the head stays the head when items are inserted or removed
    elsewhere. Each of them that succeeds writes back a start inside the container.

    The immutable view returned by AsImmutable is revoked by every change of what this object
    reads: every call to SetStart, even one that leaves the effective start unchanged, every change
    made through this object, and every change of the container made through the framework. A
    container changed outside the framework, such as a Python list wrapped without being copied,
    escapes revocation. The read-only view returned by AsReadOnly stays live.
    """

    def __init__(self, items: TList, start: int) -> None:
        super().__init__()

        container: ITuple[TItem] = self._AsContainer(items)
        count: int = container.GetCount()
        
        self.__list: TList = items
        self.__start: int = start % count if count > 0 else 0

        Finalizer(self, container.GetCollectionMonitors().RegisterMonitor(self._GetCollectionRegistries()).Remove)
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(self.GetCircularIndex(key))
    
    @final
    def _GetKey(self, key: slice) -> slice:
        def getIndex(index: int) -> int: return index if index == count else self.GetCircularIndex(index)
        
        count = self.GetCount()
        start, stop, step = key.indices(count)
        
        return slice(getIndex(start), getIndex(stop), step)

    @final
    def TryGetSourceMutability(self) -> Mutability|None:
        return self._GetInnerContainer().GetSourceMutability()
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int: return self.__start % count if (count := self.GetCount()) > 0 else 0
    @final
    def SetStart(self, start: int = 0) -> None:
        self.__start = start

        self._InvalidateViews()
    
    def ToString(self) -> str:
        def getChars() -> tuple[str, str]:
            match self.GetMutability():
                case Mutability.ReadOnly: return ('(', ')')
                
                case _: return ('[', ']')

        action: Method[TItem]|None = None

        def write(item: TItem) -> None:
            nonlocal action

            def _write(item: TItem) -> None: stream.Write(repr(item))
            def write(item: TItem) -> None:
                stream.Write(", ")

                _write(item)

            action = write

            _write(item)

        chars: tuple[str, str] = getChars()
        stream: IMemoryTextStream = MemoryTextStream()
        action = write
        result: str = ''

        with stream:
            stream.Open()

            stream.Write(chars[0])

            for item in self.AsIterable(): action(item)

            stream.Write(chars[1])

            result = stream.ToString()

        return result
class CircularBase[TItem, TList](CircularAbstract[TItem, TList], TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], IStringable, GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]: return GetItems(self, index)

class CircularTuple[T](CircularBase[T, ITuple[T]], Tuple[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(self._GetKey(key))
class CircularEquatableTuple[T: EquatableProtocol](CircularBase[T, IEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool: return self is item
class CircularHashableTuple[T: HashableProtocol](CircularBase[T, IHashableTuple[T]], HashableTuple[T], ICircularHashableTuple[T], IGenericConstraintImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T], start: int) -> None: super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool: return self is item
    def Hash(self) -> int: return self._GetContainer().Hash()

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], GenericSpecializedConstraint[TList, ITuple[TItem], IArray[TItem]], ArrayBase[TItem, TList], ICircularArray[TItem]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> bool:
        return self._GetSpecializedContainer().TrySetAt(self.GetCircularIndex(key), value)
class CircularArray[T](CircularArrayBase[T, IArray[T]], Array[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return self._GetContainer().SliceAt(self._GetKey(key))
class CircularList[T](CircularAbstract[T, IList[T]], List[T], MutableSequence[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], start: int) -> None: super().__init__(items, start)
    
    @final
    def __IsIndexValid(self, l: IList[T], index: int) -> int:
        return index if (index := self.GetCircularIndex(index, True)) < l.GetCount() else -2

    @final
    def __Move(self, x: int, y: int, action: Converter[IList[T], IndexedValueAction[int]]) -> None: action(self._GetContainer())(self.GetCircularIndex(x), self.GetCircularIndex(y))

    @final
    def __TryInsertAt[U](self, index: int, items: U, add: Converter[IList[T], Converter[U, bool|None]], insert: Converter[IList[T], IndexedValueFunction[U, bool|None]], forceUpdate: bool) -> bool|None:
        def tryInsert() -> bool|None:
            nonlocal index

            def tryInsert(inserted: bool, shift: bool) -> bool:
                if inserted: self.SetStart(start + self.GetCount() - count if shift else start)

                return inserted

            l: IList[T] = self._GetContainer()
            count: int = self.GetCount()
            start: int = self.GetStart()

            if count == 0: return tryInsert(add(l)(items) is True or forceUpdate, False)

            match (index := self.__IsIndexValid(l, index)):
                case -1: return tryInsert(insert(l)(start, items) is True or forceUpdate, True)
                case -2: return add(l)(items)

                case _: return tryInsert(insert(l)(index, items) is True or forceUpdate, index < start)
        
        return tryInsert() is True if self.ValidateIndex(index, True) else None

    @final
    def __TryInsert[U](self, index: int, items: U, add: Converter[IList[T], Converter[U, bool|None]], insert: Converter[IList[T], IndexedValueFunction[U, bool|None]]) -> bool:
        return self.__TryInsertAt(index, items, add, insert, False) is True
    @final
    def __Insert[U](self, index: int, items: U, add: Converter[IList[T], Method[U]], insert: Converter[IList[T], IndexedValueAction[U]]) -> None:
        if self.__TryInsertAt(index, items, add, insert, True) is None: raise IndexError(index)
    
    @final
    def _GetIndexOrKey(self, index: SupportsIndex|slice) -> SupportsIndex|slice:
        return self.GetCircularIndex(int(index)) if isinstance(index, SupportsIndex) else self._GetKey(index)

    @final
    def _Move(self, x: int, y: int) -> None: self.__Move(x, y, lambda l: l.Move)
    @final
    def _Swap(self, x: int, y: int) -> None: self.__Move(x, y, lambda l: l.Swap)
    
    @final
    def _SetAt(self, key: int, value: T) -> bool: return self._GetContainer().TrySetAt(self.GetCircularIndex(key), value)
    
    @final
    def _TryInsert(self, index: int, value: T) -> bool: return self.__TryInsert(index, value, lambda l: l.TryAdd, lambda l: l.TryInsert)
    @final
    def _Insert(self, index: int, value: T) -> None: self.__Insert(index, value, lambda l: l.Add, lambda l: l.Insert)
    
    @final
    def _TryInsertRange(self, index: int, items: Iterable[T]) -> bool: return self.__TryInsert(index, items, lambda l: l.TryAddRange, lambda l: l.TryInsertRange)
    @final
    def _InsertRange(self, index: int, items: Iterable[T]) -> None: self.__Insert(index, items, lambda l: l.AddRange, lambda l: l.InsertRange)

    @final
    def _Reverse(self) -> None: self._GetContainer().AsMutableSequence().reverse()

    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable

    @final
    def CanSetRange(self, indices: range, items: ICountableEnumerable[T]) -> bool: return self._GetContainer().CanSetRange(indices, items)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        position: int|None = self.TryGetCircularIndex(index)

        if position is None or position < 0: return None

        start: int = self.GetStart()

        if self._GetContainer().TryRemoveAt(position) is True:
            if position < start: start -= 1

            self.SetStart(start if start < self.GetCount() else 0)

            return True

        return False
    
    @final
    def Clear(self) -> None: self._GetContainer().Clear()
    
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
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None: SetItems(self, self._GetIndexOrKey(index), value)
    
    @final
    def __delitem__(self, index: int|slice) -> None: RemoveItems(self, self._GetIndexOrKey(index))