from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import Self, final, overload, SupportsIndex

from WinCopies import IInterface, IStringable, Abstract, IsTrue
from WinCopies.Collections.Abstraction.Selection.Enumeration import CreateCountableEnumerable
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable, IEnumerator
from WinCopies.Collections.Enumeration.Resumable import IResumableEnumerator
from WinCopies.Collections.Extensions import ICollectionMonitors, ITuple, IEquatableTuple, IHashableTuple, IArray, IList, Sequence, MutableSequence, GetViewString, AreTuplesEqual, GetTupleHash
from WinCopies.Collections.Extensions.Collection import (IManagedCollection,
                                                         TupleAbstract, TupleBase,
                                                         ArrayBase,
                                                         Tuple, EquatableTuple, HashableTuple,
                                                         MutableTuple, MutableEquatableTuple,
                                                         Array, List)
from WinCopies.Collections.Linked.Singly import IReadOnlyCountableEnumerableQueue, IReadOnlyCountableEnumerableStack, ICountableEnumerableQueue, ICountableEnumerableStack
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Collections.Util import GetSequenceInsertionIndex, ThrowIndexError
from WinCopies.Typing import INullable
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import EqualityComparison, Method, Converter, IndexedValueAction, IndexedValueFunction, IFunction
from WinCopies.Typing.Generic import IContainer, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation
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

        if result is None: ThrowIndexError(index)

        return result
class ICircularEquatableTuple[T: EquatableProtocol](ICircularTuple[T], IEquatableTuple[T]):
    def __init__(self) -> None: super().__init__()
class ICircularHashableTuple[T: HashableProtocol](ICircularEquatableTuple[T], IHashableTuple[T]):
    def __init__(self) -> None: super().__init__()

class ICircularArray[T](IArray[T], ICircularTuple[T]):
    def __init__(self) -> None: super().__init__()
class ICircularList[T](IList[T], ICircularArray[T]):
    def __init__(self) -> None: super().__init__()

class IRotatableTuple[T](ICircularTuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def SetStart(self, start: int = 0) -> None:
        ...

    @abstractmethod
    def AsCircular(self) -> ICircularTuple[T]:
        ...
class IRotatableEquatableTuple[T: EquatableProtocol](ICircularEquatableTuple[T], IRotatableTuple[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsCircular(self) -> ICircularEquatableTuple[T]:
        ...

class IRotatableArray[T](ICircularArray[T], IRotatableTuple[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsCircular(self) -> ICircularArray[T]:
        ...
class IRotatableList[T](ICircularList[T], IRotatableArray[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsCircular(self) -> ICircularList[T]:
        ...

class RotatableArrayAbstract[TItem, TList](IRotatableArray[TItem], GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateCircularArray(self) -> ICircularArray[TItem]: return _CircularArray[TItem](self, self._GetInnerContainer())
class RotatableListBase[T](IRotatableList[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetSource(self) -> IList[T]:
        ...

    @final
    def _CreateCircularList(self) -> ICircularList[T]: return _CircularList[T](self, self._GetSource())

class _CircularTupleAbstract[TItem, TList, TSource](Abstract, ICircularTuple[TItem], GenericConstraint[TList, ICircularTuple[TItem]]):
    def __init__(self, items: TList, source: TSource) -> None:
        super().__init__()

        self.__items: TList = items
        self.__source: TSource = source

    @final
    def _GetContainer(self) -> TList: return self.__items

    @final
    def _GetSource(self) -> TSource:
        return self.__source
    @abstractmethod
    def _GetSourceAsTuple(self, source: TSource) -> ITuple[TItem]:
        ...

    @final
    def GetCollectionMonitors(self) -> ICollectionMonitors: return self._GetInnerContainer().GetCollectionMonitors()

    @final
    def GetStart(self) -> int: return self._GetInnerContainer().GetStart()

    @final
    def GetMutability(self) -> Mutability: return self._GetInnerContainer().GetMutability()
    @final
    def TryGetSourceMutability(self) -> Mutability|None: return self._GetInnerContainer().TryGetSourceMutability()

    @final
    def GetCount(self) -> int: return self._GetSourceAsTuple(self._GetSource()).GetCount()

    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)

    @final
    def FindFirstIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindFirstIndex(item, predicate)
    @final
    def FindLastIndex(self, item: TItem, predicate: EqualityComparison[TItem]|None = None) -> int: return self._GetInnerContainer().FindLastIndex(item, predicate)

    @final
    def TryGetValue(self, key: int) -> INullable[TItem]: return self._GetInnerContainer().TryGetValue(key)

    @final
    def TryGetEnumerator(self) -> IEnumerator[TItem]|None: return self._GetInnerContainer().TryGetEnumerator()
    @final
    def TryGetResumableEnumerator(self) -> IResumableEnumerator[TItem]|None: return self._GetInnerContainer().TryGetResumableEnumerator()

    @final
    def ToString(self) -> str: return self._GetInnerContainer().ToString()
class _CircularTupleBase[TItem, TList](_CircularTupleAbstract[TItem, TList, ITuple[TItem]], Sequence[TItem]):
    def __init__(self, items: TList, source: ITuple[TItem]) -> None: super().__init__(items, source)

    @final
    def _GetSourceAsTuple(self, source: ITuple[TItem]) -> ITuple[TItem]: return source

    @final
    def AsQueuedCursor(self) -> IReadOnlyCountableEnumerableQueue[TItem]: return self._GetInnerContainer().AsQueuedCursor()
    @final
    def AsStackedCursor(self) -> IReadOnlyCountableEnumerableStack[TItem]: return self._GetInnerContainer().AsStackedCursor()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]: return GetItems(self, index)

@final
class _CircularTuple[T](_CircularTupleBase[T, IRotatableTuple[T]], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: IRotatableTuple[T], source: ITuple[T], reversed: ICircularTuple[T]|None = None) -> None:
        def createReversed() -> ITuple[T]:
            if reversed is None:
                _reversed: ITuple[T] = items.AsReversed()
    
                return _CircularTuple[T](_reversed, source, self) if isinstance(_reversed, IRotatableEquatableTuple) else _reversed # TODO: Reversed view should implement ICircularTuple
            
            return reversed
        
        super().__init__(items, source)

        self.__reversed: ITuple[T] = createReversed()

    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetContainer().SliceAt(key)

    def AsReversed(self) -> ITuple[T]: return self.__reversed

    def AsReadOnly(self) -> ITuple[T]: return self
    def AsImmutable(self) -> ITuple[T]: return self._GetContainer().AsImmutable()
@final
class _CircularEquatableTuple[T](_CircularTupleBase[T, IRotatableEquatableTuple[T]], ICircularEquatableTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: IRotatableEquatableTuple[T], source: ITuple[T], reversed: ICircularEquatableTuple[T]|None = None) -> None:
        def createReversed() -> IEquatableTuple[T]:
            if reversed is None:
                _reversed: IEquatableTuple[T] = items.AsReversed()
    
                return _CircularEquatableTuple[T](_reversed, source, self) if isinstance(_reversed, IRotatableEquatableTuple) else _reversed # TODO: Reversed view should implement ICircularEquatableTuple
            
            return reversed

        super().__init__(items, source)

        self.__reversed: IEquatableTuple[T] = createReversed()

    def Equals(self, item: Self|object) -> bool: return self._GetContainer().Equals(item)

    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(key)

    def AsReversed(self) -> IEquatableTuple[T]: return self.__reversed

    def AsReadOnly(self) -> IEquatableTuple[T]: return self
    def AsImmutable(self) -> IEquatableTuple[T]: return self._GetContainer().AsImmutable()

class _ICircularArray[TItem, TList](ICircularArray[TItem], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self) -> None: super().__init__()

    def _Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    def _Swap(self, x: int, y: int) -> None: self._GetSpecializedContainer().Swap(x, y)

    def _TrySetAt(self, key: int, value: TItem, throwOnError: bool) -> bool|None:
        container: ICircularArray[TItem] = self._GetSpecializedContainer()

        return (container.SetAt if throwOnError else container.TrySetAt)(key, value)

@final
class _CircularArray[T](_CircularTupleBase[T, IRotatableArray[T]], _ICircularArray[T, IRotatableArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], IRotatableArray[T]]):
    def __init__(self, items: IRotatableArray[T], source: ITuple[T], reversed: ICircularArray[T]|None = None) -> None:
        def createReversed() -> IArray[T]:
            if reversed is None:
                _reversed: IArray[T] = items.AsReversed()
    
                return _CircularArray[T](_reversed, source, self) if isinstance(_reversed, IRotatableArray) else _reversed # TODO: Reversed view should implement ICircularArray
            
            return reversed

        super().__init__(items, source)

        self.__reversed: IArray[T] = createReversed()

    def SliceAt(self, key: slice) -> IArray[T]: return self._GetContainer().SliceAt(key)

    def AsReversed(self) -> IArray[T]: return self.__reversed

    def AsReadOnly(self) -> IArray[T]: return self
    def AsImmutable(self) -> ITuple[T]: return self._GetContainer().AsImmutable()
@final
class _CircularList[T](_CircularTupleAbstract[T, IRotatableList[T], IList[T]], MutableSequence[T], _ICircularArray[T, IRotatableList[T]], ICircularList[T], IGenericConstraintImplementation[ICircularList[T]]):
    def __init__(self, items: IRotatableList[T], source: IList[T], reversed: ICircularList[T]|None = None) -> None:
        def createViews() -> tuple[IArray[T], IList[T]]:
            if reversed is None:
                fixedSize: IArray[T] = items.AsFixedSize()
                _reversed: IList[T] = items.AsReversed()
    
                return (_CircularArray[T](fixedSize, source, self) if isinstance(fixedSize, IRotatableArray) else fixedSize, _CircularList[T](_reversed, source, self) if isinstance(_reversed, IRotatableList) else _reversed) # TODO: Reversed view should implement ICircularList
            
            return (items.AsFixedSize(), reversed)

        super().__init__(items, source)

        fixedSize, _reversed = createViews()

        self.__fixedSize: IArray[T] = fixedSize
        self.__reversed: IList[T] = _reversed

    def _AsSpecialized(self, container: IRotatableList[T]) -> ICircularArray[T]: return container

    def _GetSourceAsTuple(self, source: ITuple[T]) -> ITuple[T]: return source

    def _Insert(self, index: int, value: T) -> None: self._GetContainer().Insert(index, value)
    def _InsertRange(self, index: int, items: Iterable[T]) -> None: self._GetContainer().InsertRange(index, items)

    def _Reverse(self) -> None: self._GetContainer().AsMutableSequence().reverse()

    def CanSetRange(self, indices: ICountableEnumerable[int], items: ICountableEnumerable[T], throwOnError: bool = False) -> bool: return self._GetContainer().CanSetRange(indices, items, throwOnError)

    def TryRemoveAt(self, index: int) -> bool|None: return self._GetContainer().TryRemoveAt(index)

    def Clear(self) -> None: self._GetSource().Clear()

    def SliceAt(self, key: slice) -> IList[T]: return self._GetContainer().SliceAt(key)

    def AsReversed(self) -> IList[T]: return self.__reversed

    def AsQueuedCursor(self) -> ICountableEnumerableQueue[T]: return self._GetContainer().AsQueuedCursor()
    def AsStackedCursor(self) -> ICountableEnumerableStack[T]: return self._GetContainer().AsStackedCursor()

    def AsFixedSize(self) -> IArray[T]: return self.__fixedSize
    def AsReadOnly(self) -> IList[T]: return self
    def AsImmutable(self) -> ITuple[T]: return self._GetContainer().AsImmutable()

    def insert(self, index: int, value: T) -> None: self._GetContainer()
    
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

class _ICircular(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetKey(self, key: slice) -> slice:
        ...
    @abstractmethod
    def _SetStart(self, start: int = 0) -> None:
        ...

class _CircularAbstract[TItem, TList](TupleAbstract[TItem], ICircularTuple[TItem], IManagedCollection[TItem], IStringable, _ICircular, GenericConstraint[TList, ITuple[TItem]]):
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
    def _GetContainer(self) -> TList: return self.__list
    
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
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        count: int = self.GetCount()
        
        return self.__start % count if count > 0 else 0
    @final
    def _SetStart(self, start: int = 0) -> None:
        self.__start = start

        self._InvalidateViews()
    
    def ToString(self) -> str: return GetViewString(self, self._GetInnerContainer())

class CircularAbstract[TItem, TList](_CircularAbstract[TItem, TList]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self._GetInnerContainer().GetSourceMutability()
class RotatableAbstract[TItem, TList](_CircularAbstract[TItem, TList], IRotatableTuple[TItem]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return max(self._GetInnerContainer().GetSourceMutability(), Mutability.FixedSize)
    
    def SetStart(self, start: int = 0) -> None: return self._SetStart(start)

class _CircularBase[TItem, TList](TupleBase[TItem], Sequence[TItem], IStringable, GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]: return GetItems(self, index)

class _ReadOnlyCircularBase[TItem, TList](_CircularAbstract[TItem, TList], _CircularBase[TItem, TList]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self._GetInnerContainer().GetSourceMutability()

class CircularBase[TItem, TList](CircularAbstract[TItem, TList], _CircularBase[TItem, TList]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
class RotatableBase[TItem, TList](RotatableAbstract[TItem, TList], _CircularBase[TItem, TList]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)

class CircularTuple[T](CircularBase[T, ITuple[T]], Tuple[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(self._GetKey(key))
class RotatableTuple[T](RotatableBase[T, ITuple[T]], MutableTuple[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], start: int) -> None:
        def update(func: IFunction[ITuple[T]]) -> None: self.__readOnly = func
        
        super().__init__(items, start)
        
        self.__readOnly: IFunction[ITuple[T]] = self._CreateReadOnlyUpdater(update) # type: ignore[no-redef]
        self.__circular: ICircularTuple[T] = _CircularTuple[T](self, self._GetContainer())
    
    @final
    def _AsReadOnly(self) -> IFunction[ITuple[T]]: return self.__readOnly
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(self._GetKey(key))

    @final
    def AsCircular(self) -> ICircularTuple[T]: return self.__circular

class CircularEquatableTuple[T: EquatableProtocol](CircularBase[T, IEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
class RotatableEquatableTuple[T: EquatableProtocol](RotatableBase[T, IEquatableTuple[T]], MutableEquatableTuple[T], IRotatableEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T], start: int) -> None:
        def update(func: IFunction[IEquatableTuple[T]]) -> None: self.__readOnly = func
        
        super().__init__(items, start)
        
        self.__readOnly: IFunction[IEquatableTuple[T]] = self._CreateReadOnlyUpdater(update) # type: ignore[no-redef]
        self.__circular: ICircularEquatableTuple[T] = _CircularEquatableTuple[T](self, self._GetContainer())
    
    @final
    def _AsReadOnly(self) -> IFunction[IEquatableTuple[T]]: return self.__readOnly
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)

    @final
    def AsCircular(self) -> ICircularEquatableTuple[T]: return self.__circular

class CircularHashableTuple[T: HashableProtocol](_ReadOnlyCircularBase[T, IHashableTuple[T]], HashableTuple[T], ICircularHashableTuple[T], IGenericConstraintImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T], start: int) -> None: super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
    def Hash(self) -> int: return GetTupleHash(self)

class _CircularArrayBase[TItem, TList](ArrayBase[TItem, TList], ICircularArray[TItem], GenericSpecializedConstraint[TList, ITuple[TItem], IArray[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _SetAt(self, key: int, value: TItem, throwOnError: bool) -> bool:
        items: IArray[TItem] = self._GetSpecializedContainer()

        return IsTrue((items.SetAt if throwOnError else items.TrySetAt)(self.GetCircularIndex(key), value))

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], _CircularArrayBase[TItem, TList]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)
class RotatableArrayBase[TItem, TList](RotatableBase[TItem, TList], _CircularArrayBase[TItem, TList], IRotatableArray[TItem]):
    def __init__(self, items: TList, start: int) -> None: super().__init__(items, start)

class CircularArray[T](CircularArrayBase[T, IArray[T]], Array[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], start: int) -> None: super().__init__(items, start)

    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return self._GetContainer().SliceAt(self._GetKey(key))
class RotatableArray[T](RotatableArrayBase[T, IArray[T]], RotatableArrayAbstract[T, IArray[T]], Array[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], start: int) -> None:
        super().__init__(items, start)

        self.__circular: ICircularArray[T] = self._CreateCircularArray()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]: return self._GetContainer().SliceAt(self._GetKey(key))

    @final
    def AsCircular(self) -> ICircularArray[T]: return self.__circular

class _CircularListBase[T](List[T], MutableSequence[T], ICircularList[T], _ICircular, IContainer[IList[T]]):
    def __init__(self) -> None: super().__init__()
    
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
                if inserted: self._SetStart(start + self.GetCount() - count if shift else start)

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
        if self.__TryInsertAt(index, items, add, insert, True) is None: ThrowIndexError(index)
    
    @final
    def _GetIndexOrKey(self, index: SupportsIndex|slice) -> SupportsIndex|slice:
        return self.GetCircularIndex(int(index)) if isinstance(index, SupportsIndex) else self._GetKey(index)

    @final
    def _Move(self, x: int, y: int) -> None: self.__Move(x, y, lambda l: l.Move)
    @final
    def _Swap(self, x: int, y: int) -> None: self.__Move(x, y, lambda l: l.Swap)
    
    @final
    def _SetAt(self, key: int, value: T, throwOnError: bool) -> bool:
        items: IArray[T] = self._GetContainer()
        
        return IsTrue((items.SetAt if throwOnError else items.TrySetAt)(self.GetCircularIndex(key), value))
    
    @final
    def _TryInsert(self, index: int, value: T) -> bool: return self.__TryInsert(index, value, lambda l: l.TryAdd, lambda l: l.TryInsert)
    @final
    def _Insert(self, index: int, value: T) -> None: self.__Insert(index, value, lambda l: l.Add, lambda l: l.Insert)
    
    @final
    def _TryInsertRange(self, index: int, items: Iterable[T]) -> bool: return self.__TryInsert(index, items, lambda l: l.TryAddRange, lambda l: l.TryInsertRange)
    @final
    def _InsertRange(self, index: int, items: Iterable[T]) -> None: self.__Insert(index, items, lambda l: l.AddRange, lambda l: l.InsertRange)

    # Position k read position (start + k) % count of the container, which the reversal sends to
    # count - 1 - (start + k) % count. Read from count - start, the list finds it at count - 1 - k,
    # which is what reversing the list means. Written back inside the container, as every change
    # through the list writes its start.
    @final
    def _Reverse(self) -> None:
        start: int = self.GetStart()

        self._GetContainer().AsMutableSequence().reverse()
        self._SetStart(self.GetCount() - start if start > 0 else 0)

    # The span is this view's, the question the container's, so each position is translated
    # before it is asked: handed over as they were, the positions named other items than those
    # leaving, and a span the container refused went through its removal first. A refusal
    # comes back as it is, the error of no cause naming a position.
    @final
    def CanSetRange(self, indices: ICountableEnumerable[int], items: ICountableEnumerable[T], throwOnError: bool = False) -> bool:
        return self._GetContainer().CanSetRange(CreateCountableEnumerable(indices, self.GetCircularIndex), items, throwOnError)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]: return self._GetContainer().SliceAt(self._GetKey(key))
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        position: int|None = self.TryGetCircularIndex(index)

        if position is None or position < 0: return None

        start: int = self.GetStart()

        if self._GetContainer().TryRemoveAt(position) is True:
            if position < start: start -= 1

            self._SetStart(start if start < self.GetCount() else 0)

            return True

        return False
    
    @final
    def Clear(self) -> None: self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: T) -> None: self.Insert(GetSequenceInsertionIndex(index, self.GetCount()), value)
    
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

class CircularList[T](CircularAbstract[T, IList[T]], _CircularListBase[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], start: int) -> None: super().__init__(items, start)
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable
class RotatableList[T](RotatableAbstract[T, IList[T]], _CircularListBase[T], RotatableListBase[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], start: int) -> None:
        super().__init__(items, start)

        self.__circular: ICircularList[T] = self._CreateCircularList()

    @final
    def _GetSource(self) -> IList[T]: return self._GetContainer()
    
    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable

    @final
    def AsCircular(self) -> ICircularList[T]: return self.__circular