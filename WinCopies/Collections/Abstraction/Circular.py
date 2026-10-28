from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase, MutableSequence as MutableSequenceBase
from typing import overload, final, SupportsIndex

from WinCopies import IsTrue
from WinCopies.Collections.Circular import (ICircularTuple, ICircularEquatableTuple, ICircularHashableTuple, ICircularArray, ICircularList,
                                            IRotatableTuple, IRotatableEquatableTuple, IRotatableArray, IRotatableList,
                                            RotatableArrayAbstract as _RotatableArrayAbstract, RotatableListBase)
from WinCopies.Collections.Core import Mutability
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable
from WinCopies.Collections.Extensions import (IReadOnlyLinkedCursorProvider, ILinkedCursorProvider,
                                              ITuple, IEquatableTuple, IHashableTuple, IArray, IList,
                                              Sequence, SequenceAbstract, MutableSequenceAbstract,
                                              GetViewString, AreTuplesEqual, GetTupleHash)
from WinCopies.Collections.Extensions.Collection import (IReadOnlyCursorProvider, ICursorProvider,
                                                         TupleBase, ArrayBase, MutableList, ReversedListAbstract, ReversedArrayBase,
                                                         Tuple, EquatableTuple, HashableTuple,
                                                         MutableTuple, MutableEquatableTuple)
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Collections.Util import GetSequenceInsertionIndex
from WinCopies.Typing.Comparison import EquatableProtocol, HashableProtocol
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater
from WinCopies.Typing.Generic import IContainer, GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class CircularAbstract[TItem, TList](TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], GenericConstraint[TList, ICircularTuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()
        
        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList: return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    
    @final
    def TryGetSourceMutability(self) -> Mutability: return self._GetInnerContainer().GetSourceMutability()
    
    @final
    def Contains(self, value: TItem|object) -> bool: return self._GetInnerContainer().Contains(value)
    
    @final
    def GetCount(self) -> int: return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int: return self._GetInnerContainer().GetStart()
    
    def ToString(self) -> str: return GetViewString(self, self._GetInnerContainer())
class RotatableAbstract[TItem, TList](CircularAbstract[TItem, TList], IRotatableTuple[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)

    @abstractmethod
    def _GetContainerAsRotatable(self, items: TList) -> IRotatableTuple[TItem]:
        ...

    def SetStart(self, start: int = 0) -> None: self._GetContainerAsRotatable(self._GetContainer()).SetStart(start)

class _CircularBase[T](Sequence[T], ITuple[T]):
    def __init__(self) -> None: super().__init__()
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[T]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> T|SequenceBase[T]: return GetItems(self, index)

class CircularBase[TItem, TList](CircularAbstract[TItem, TList], _CircularBase[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)
class RotatableBase[TItem, TList](RotatableAbstract[TItem, TList], _CircularBase[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)

class _CircularTuple[T](IReadOnlyCursorProvider[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def GetMutability(self) -> Mutability: return Mutability.ReadOnly

class CircularTuple[T](CircularBase[T, ICircularTuple[T]], Tuple[T], _CircularTuple[T], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: ICircularTuple[T]) -> None: super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(key)
class RotatableTuple[T](RotatableBase[T, IRotatableTuple[T]], MutableTuple[T], _CircularTuple[T], IGenericConstraintImplementation[IRotatableTuple[T]]):
    def __init__(self, items: IRotatableTuple[T]) -> None: super().__init__(items)

    @final
    def _GetContainerAsRotatable(self, items: IRotatableTuple[T]) -> IRotatableTuple[T]: return items

    @final
    def SliceAt(self, key: slice) -> ITuple[T]: return self._GetInnerContainer().SliceAt(key)

class CircularEquatableTuple[T: EquatableProtocol](CircularBase[T, ICircularEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], _CircularTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T]) -> None: super().__init__(items)

    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(key)
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
class RotatableEquatableTuple[T: EquatableProtocol](RotatableBase[T, IRotatableEquatableTuple[T]], MutableEquatableTuple[T], _CircularTuple[T], IReadOnlyCursorProvider[T], IGenericConstraintImplementation[IRotatableEquatableTuple[T]]):
    def __init__(self, items: IRotatableEquatableTuple[T]) -> None: super().__init__(items)

    @final
    def _GetContainerAsRotatable(self, items: IRotatableTuple[T]) -> IRotatableTuple[T]: return items

    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]: return self._GetContainer().SliceAt(key)
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)

class CircularHashableTuple[T: HashableProtocol](CircularBase[T, ICircularHashableTuple[T]], HashableTuple[T], ICircularHashableTuple[T], IReadOnlyCursorProvider[T], IGenericConstraintImplementation[ICircularHashableTuple[T]]):
    def __init__(self, items: ICircularHashableTuple[T]) -> None: super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]: return self._GetContainer().SliceAt(key)
    
    def Equals(self, item: object) -> bool: return AreTuplesEqual(self, item)
    def Hash(self) -> int: return GetTupleHash(self)

class _ReversedArrayBase[TItem, TList](ReversedArrayBase[TItem, TList, IArray[TItem]], SequenceAbstract[TItem], ICircularArray[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)

    @abstractmethod
    def _GetContainerAsCircular(self, container: TList) -> ICircularArray[TItem]:
        ...
    @final
    def __AsCircular(self) -> ICircularArray[TItem]:
        return self._GetContainerAsCircular(self._GetContainer())

    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def GetStart(self) -> int: return self.__AsCircular().GetStart()
    
    @final
    def AsReversed(self) -> ICircularArray[TItem]: return self.__AsCircular()
    
    @final
    def _SliceAt(self, key: slice) -> IArray[TItem]: return self._GetSpecializedContainer().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IArray[TItem]: return self._ToSlicedAt(key)

class _CircularArrayAbstract[TItem, TList](ICircularArray[TItem], IContainer[TList]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetContainerAsArray(self, container: TList) -> ICircularArray[TItem]:
        ...
class _RotatableArray[TItem, TList](_CircularArrayAbstract[TItem, TList], IRotatableArray[TItem]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetContainerAsArray(self, container: TList) -> IRotatableArray[TItem]:
        ...

    @final
    def SetStart(self, start: int = 0) -> None: self._GetContainerAsArray(self._GetContainer()).SetStart(self.ReverseIndex(start))

@final
class _ReversedArray[T](_ReversedArrayBase[T, ICircularArray[T]], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T]) -> None: super().__init__(items)

    def _GetContainerAsCircular(self, container: ICircularArray[T]) -> ICircularArray[T]: return container
@final
class _ReversedRotatableArray[T](_ReversedArrayBase[T, IRotatableArray[T]], _RotatableArray[T, IRotatableArray[T]], _RotatableArrayAbstract[T, IRotatableArray[T]], IGenericSpecializedConstraintImplementation[ITuple[T], IRotatableArray[T]]):
    def __init__(self, items: IRotatableArray[T]) -> None: super().__init__(items)

    def _GetContainerAsArray(self, container: IRotatableArray[T]) -> IRotatableArray[T]: return container
    def _GetContainerAsCircular(self, container: IRotatableArray[T]) -> IRotatableArray[T]: return container

    def AsCircular(self) -> ICircularArray[T]: return self._CreateCircularArray()

@final
class _ArrayUpdater[T](ValueFunctionUpdater[ICircularArray[T]]):
    def __init__(self, array: ICircularArray[T], updater: Method[IFunction[ICircularArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: ICircularArray[T] = array
    
    def _GetValue(self) -> ICircularArray[T]: return _ReversedArray[T](self.__array)
@final
class _RotatableArrayUpdater[T](ValueFunctionUpdater[IRotatableArray[T]]):
    def __init__(self, array: IRotatableArray[T], updater: Method[IFunction[IRotatableArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: IRotatableArray[T] = array
    
    def _GetValue(self) -> IRotatableArray[T]: return _ReversedRotatableArray[T](self.__array)

class _ReversedListBase[TItem, TList](ReversedListAbstract[TItem, TList, IList[TItem]], _CircularArrayAbstract[TItem, TList], MutableSequenceAbstract[TItem], ICircularList[TItem]):
    def __init__(self, items: TList) -> None: super().__init__(items)

    @final    
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    @final
    def GetStart(self) -> int: return self._GetContainerAsArray(self._GetContainer()).GetStart()

    @final
    def _GetSpecializedContainerAsList(self, container: IList[TItem]) -> IList[TItem]: return container
    
    @final
    def _SliceAt(self, key: slice) -> IList[TItem]: return self._GetContainerAsList().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IList[TItem]: return self._ToSlicedAt(key)

@final
class _ReversedList[T](_ReversedListBase[T, ICircularList[T]], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T]) -> None: super().__init__(items)
    
    def _GetContainerAsArray(self, container: ICircularArray[T]) -> ICircularArray[T]: return container
    def _GetInnerContainerAsList(self, container: ICircularList[T]) -> ICircularList[T]: return container
@final
class _ReversedRotatableList[T](_ReversedListBase[T, IRotatableList[T]], _RotatableArray[T, IRotatableList[T]], RotatableListBase[T], IGenericSpecializedConstraintImplementation[ITuple[T], IRotatableList[T]]):
    def __init__(self, items: IRotatableList[T]) -> None: super().__init__(items)

    def _GetSource(self) -> IList[T]: return self._GetContainer()

    def _GetContainerAsArray(self, container: IRotatableArray[T]) -> IRotatableArray[T]: return container
    def _GetInnerContainerAsList(self, container: ICircularList[T]) -> ICircularList[T]: return container

    def AsCircular(self) -> ICircularList[T]: return self._CreateCircularList()

@final
class _ListUpdater[T](ValueFunctionUpdater[ICircularList[T]]):
    def __init__(self, array: ICircularList[T], updater: Method[IFunction[ICircularList[T]]]) -> None:
        super().__init__(updater)

        self.__array: ICircularList[T] = array
    
    def _GetValue(self) -> ICircularList[T]: return _ReversedList[T](self.__array)
@final
class _RotatableListUpdater[T](ValueFunctionUpdater[IRotatableList[T]]):
    def __init__(self, array: IRotatableList[T], updater: Method[IFunction[IRotatableList[T]]]) -> None:
        super().__init__(updater)

        self.__array: IRotatableList[T] = array
    
    def _GetValue(self) -> IRotatableList[T]: return _ReversedRotatableList[T](self.__array)

class CircularArrayAbstract[TItem, TList](ArrayBase[TItem, TList], ICircularArray[TItem], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Move(self, x: int, y: int) -> None: self._GetSpecializedContainer().Move(x, y)
    @final
    def _Swap(self, x: int, y: int) -> None: self._GetSpecializedContainer().Swap(x, y)
    
    @final
    def _SetAt(self, key: int, value: TItem, throwOnError: bool) -> bool:
        items: ICircularArray[TItem] = self._GetSpecializedContainer()

        return IsTrue((items.SetAt if throwOnError else items.TrySetAt)(key, value))
class RotatableArrayAbstract[TItem, TList](CircularArrayAbstract[TItem, TList], IRotatableArray[TItem]):
    def __init__(self) -> None: super().__init__()

class _CircularArrayBase[TItem, TList](CircularArrayAbstract[TItem, TList], IReadOnlyCursorProvider[TItem]):
    def __init__(self) -> None: super().__init__()

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], _CircularArrayBase[TItem, TList]):
    def __init__(self, items: TList) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TItem]]) -> None: self.__cursorProvider = func
        
        super().__init__(items)
        
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TItem]] = self._CreateCursorProvider(update) # type: ignore[no-redef]
    
    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TItem]]: return self.__cursorProvider
class RotatableArrayBase[TItem, TList](RotatableBase[TItem, TList], RotatableArrayAbstract[TItem, TList], _CircularArrayBase[TItem, TList]):
    def __init__(self, items: TList) -> None:
        def update(func: IFunction[IReadOnlyLinkedCursorProvider[TItem]]) -> None: self.__cursorProvider = func
        
        super().__init__(items)
        
        self.__cursorProvider: IFunction[IReadOnlyLinkedCursorProvider[TItem]] = self._CreateCursorProvider(update) # type: ignore[no-redef]
    
    @final
    def _GetCursorProvider(self) -> IFunction[IReadOnlyLinkedCursorProvider[TItem]]: return self.__cursorProvider

class _CircularArray[TItem, TList](_CircularArrayBase[TItem, TList]):
    def __init__(self) -> None: super().__init__()

    @final
    def GetMutability(self) -> Mutability: return Mutability.FixedSize
    
    @final
    def AsReversed(self) -> IArray[TItem]: return self._AsSpecialized(self._AsReversed())
    
    @final
    def SliceAt(self, key: slice) -> IArray[TItem]: return self._AsSpecialized(self._GetContainer()).SliceAt(key)

class CircularArray[T](CircularArrayBase[T, ICircularArray[T]], _CircularArray[T, ICircularArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T]) -> None: super().__init__(items)
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[ICircularArray[T]]]) -> IFunction[ICircularArray[T]]: return _ArrayUpdater[T](self, func)
class RotatableArray[T](RotatableArrayBase[T, IRotatableArray[T]], _CircularArray[T, IRotatableArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], IRotatableArray[T]]):
    def __init__(self, items: IRotatableArray[T]) -> None: super().__init__(items)
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[IRotatableArray[T]]]) -> IFunction[IRotatableArray[T]]: return _RotatableArrayUpdater[T](self, func)

class _CircularList[TItem, TList](CircularArrayAbstract[TItem, TList], MutableList[TItem], ICircularList[TItem], ICursorProvider[TItem]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetContainerAsList(self, container: TList) -> ICircularList[TItem]:
        ...
    @final
    def _AsList(self) -> ICircularList[TItem]:
        return self._GetContainerAsList(self._GetContainer())

    @abstractmethod
    def _AsFixedSize(self) -> IFunction[IArray[TItem]]:
        ...

    @final
    def GetMutability(self) -> Mutability: return Mutability.Mutable
    
    @final
    def CanSetRange(self, indices: ICountableEnumerable[int], items: ICountableEnumerable[TItem], throwOnError: bool = False) -> bool: return self._AsList().CanSetRange(indices, items, throwOnError)
    
    @final
    def _Reverse(self) -> None: self._AsList().AsMutableSequence().reverse()
    
    @final
    def SliceAt(self, key: slice) -> IList[TItem]: return self._AsList().SliceAt(key)
    
    @final
    def _Insert(self, index: int, value: TItem) -> None: self._AsList().Insert(index, value)
    @final
    def _InsertRange(self, index: int, items: Iterable[TItem]) -> None: self._AsList().InsertRange(index, items)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None: return self._AsList().TryRemoveAt(index)
    
    @final
    def Clear(self) -> None: self._AsList().Clear()
    
    @final
    def AsFixedSize(self) -> IArray[TItem]: return self._AsFixedSize().GetValue()
    
    @final
    def AsReversed(self) -> IList[TItem]: return self._GetContainerAsList(self._AsReversed())
    
    @final
    def insert(self, index: int, value: TItem) -> None: self.Insert(GetSequenceInsertionIndex(index, self.GetCount()), value)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> MutableSequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|MutableSequenceBase[TItem]: return GetItems(self, index)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: TItem) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[TItem]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: TItem|Iterable[TItem]) -> None: SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice) -> None: RemoveItems(self, index)

class CircularList[T](CircularAbstract[T, ICircularList[T]], _CircularList[T, ICircularList[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T]) -> None:
        def updateFixedSize(func: IFunction[IArray[T]]) -> None: self.__fixedSize = func
        def updateCursorProvider(func: IFunction[ILinkedCursorProvider[T]]) -> None: self.__cursorProvider = func
        
        super().__init__(items)
        
        self.__fixedSize: IFunction[IArray[T]] = self._GetFixedSizeUpdater(updateFixedSize) # type: ignore[no-redef]
        self.__cursorProvider: IFunction[ILinkedCursorProvider[T]] = self._CreateCursorProvider(updateCursorProvider) # type: ignore[no-redef]
    
    @final
    def _GetCursorProvider(self) -> IFunction[ILinkedCursorProvider[T]]: return self.__cursorProvider
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[ICircularList[T]]]) -> IFunction[ICircularList[T]]: return _ListUpdater[T](self, func)

    @final
    def _AsFixedSize(self) -> IFunction[IArray[T]]: return self.__fixedSize

    @final
    def _GetContainerAsList(self, container: ICircularList[T]) -> ICircularList[T]: return container
class RotatableList[T](RotatableAbstract[T, IRotatableList[T]], _CircularList[T, IRotatableList[T]], RotatableArrayAbstract[T, IRotatableList[T]], IRotatableList[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], IRotatableList[T]]):
    def __init__(self, items: IRotatableList[T]) -> None:
        def updateFixedSize(func: IFunction[IArray[T]]) -> None: self.__fixedSize = func
        def updateCursorProvider(func: IFunction[ILinkedCursorProvider[T]]) -> None: self.__cursorProvider = func
        
        super().__init__(items)
        
        self.__fixedSize: IFunction[IArray[T]] = self._GetFixedSizeUpdater(updateFixedSize) # type: ignore[no-redef]
        self.__cursorProvider: IFunction[ILinkedCursorProvider[T]] = self._CreateCursorProvider(updateCursorProvider) # type: ignore[no-redef]
    
    @final
    def _GetCursorProvider(self) -> IFunction[ILinkedCursorProvider[T]]: return self.__cursorProvider
    
    @final
    def _GetReversedUpdater(self, func: Method[IFunction[IRotatableList[T]]]) -> IFunction[IRotatableList[T]]: return _RotatableListUpdater[T](self, func)

    @final
    def _AsFixedSize(self) -> IFunction[IArray[T]]: return self.__fixedSize

    @final
    def _GetContainerAsList(self, container: ICircularList[T]) -> ICircularList[T]: return container

    @final
    def _GetContainerAsRotatable(self, items: IRotatableTuple[T]) -> IRotatableTuple[T]: return items