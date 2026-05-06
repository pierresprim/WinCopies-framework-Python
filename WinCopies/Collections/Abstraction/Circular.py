from collections.abc import Iterable, Sequence as SequenceBase
from typing import overload, final, SupportsIndex

from WinCopies.Collections import Mutability
from WinCopies.Collections.Circular import ICircularTuple, ICircularEquatableTuple, ICircularHashableTuple, ICircularArray, ICircularList
from WinCopies.Collections.Extensions import IResumableEnumeratorMonitor, ITuple, IEquatableTuple, IHashableTuple, IArray, IList, Sequence, MutableSequence, SequenceAbstract, MutableSequenceAbstract
from WinCopies.Collections.Extensions.Collection import TupleBase, ArrayBase, ReversedArrayBase, Tuple, EquatableTuple, HashableTuple, ReversedListAbstract
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Typing.Comparison import IEquatableItem
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class CircularAbstract[TItem, TList](TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], GenericConstraint[TList, ICircularTuple[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__()
        
        self.__list: TList = items
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(key)
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        return self._GetInnerContainer().GetStart()
    
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
class CircularBase[TItem, TList](CircularAbstract[TItem, TList]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]:
        return GetItems(self, index)

class CircularTuple[T](CircularBase[T, ICircularTuple[T]], Tuple[T], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: ICircularTuple[T]) -> None:
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetInnerContainer().SliceAt(key)
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, ICircularEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T]) -> None:
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(key)
    
    def Equals(self, item: object) -> bool:
        return self is item
class CircularHashableTuple[T: IEquatableItem](CircularBase[T, ICircularHashableTuple[T]], HashableTuple[T], ICircularHashableTuple[T], IGenericConstraintImplementation[ICircularHashableTuple[T]]):
    def __init__(self, items: ICircularHashableTuple[T]) -> None:
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self._GetContainer().SliceAt(key)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

@final
class _ReversedArray[T](ReversedArrayBase[T, ICircularArray[T], IArray[T]], SequenceAbstract[T], ICircularArray[T], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T], factory: IResumableEnumeratorMonitor[T]) -> None:
        super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability:
        return Mutability.FixedSize
    
    def GetStart(self) -> int:
        return self._GetContainer().GetStart()
    
    @final
    def AsReversed(self) -> ICircularArray[T]:
        return self._GetContainer()
    
    @final
    def _SliceAt(self, key: slice) -> IArray[T]:
        return self._GetSpecializedContainer().SliceAt(key)
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self.ToSlicedAt(key)
@final
class _ArrayUpdater[T](ValueFunctionUpdater[ICircularArray[T]]):
    def __init__(self, array: ICircularArray[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ICircularArray[T]]]) -> None:
        super().__init__(updater)

        self.__array: ICircularArray[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ICircularArray[T]:
        return _ReversedArray[T](self.__array, self.__factory)

@final
class _ReversedList[T](ReversedListAbstract[T, ICircularList[T], IList[T]], MutableSequenceAbstract[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T], factory: IResumableEnumeratorMonitor[T]) -> None:
        super().__init__(items, factory)
    
    def GetMutability(self) -> Mutability:
        return Mutability.Mutable
    
    def GetStart(self) -> int:
        return self._GetContainer().GetStart()
    
    def _GetInnerContainerAsList(self, container: ICircularList[T]) -> ICircularList[T]:
        return container
    def _GetSpecializedContainerAsList(self, container: IList[T]) -> IList[T]:
        return container
    
    def _SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainer().SliceAt(key)
    def SliceAt(self, key: slice) -> IList[T]:
        return self.ToSlicedAt(key)

@final
class _ListUpdater[T](ValueFunctionUpdater[ICircularList[T]]):
    def __init__(self, array: ICircularList[T], factory: IResumableEnumeratorMonitor[T], updater: Method[IFunction[ICircularList[T]]]) -> None:
        super().__init__(updater)

        self.__array: ICircularList[T] = array
        self.__factory: IResumableEnumeratorMonitor[T] = factory
    
    def _GetValue(self) -> ICircularList[T]:
        return _ReversedList[T](self.__array, self.__factory)

class CircularArrayAbstract[TItem, TList](CircularAbstract[TItem, TList], ArrayBase[TItem, TList], ICircularArray[TItem], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], CircularArrayAbstract[TItem, TList]):
    def __init__(self, items: TList) -> None:
        super().__init__(items)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(key, value)
class CircularArray[T](CircularArrayBase[T, ICircularArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularArray[T]]):
    def __init__(self, items: ICircularArray[T]) -> None:
        super().__init__(items)
    
    @final
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[T], func: Method[IFunction[ICircularArray[T]]]) -> IFunction[ICircularArray[T]]:
        return _ArrayUpdater[T](self, factory, func)
    
    @final
    def AsReversed(self) -> IArray[T]:
        return self._AsReversed()
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._GetContainer().SliceAt(key)
class CircularList[T](CircularArrayAbstract[T, ICircularList[T]], MutableSequence[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularList[T]]):
    def __init__(self, items: ICircularList[T]) -> None:
        super().__init__(items)
    
    @final
    def _GetUpdater(self, factory: IResumableEnumeratorMonitor[T], func: Method[IFunction[ICircularList[T]]]) -> IFunction[ICircularList[T]]:
        return _ListUpdater[T](self, factory, func)
    
    @final
    def AsReversed(self) -> IList[T]:
        return self._AsReversed()
    
    @final
    def SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainer().SliceAt(key)
    
    @final
    def Add(self, item: T) -> None:
        self._GetContainer().Add(item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self._GetContainer().TryInsert(index, value)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(index)
    
    @final
    def Clear(self) -> None:
        self._GetContainer().Clear()
    
    @final
    def insert(self, index: int, value: T) -> None:
        self.Insert(index, value)
    
    @overload
    def __setitem__(self, index: SupportsIndex, value: T) -> None: ...
    @overload
    def __setitem__(self, index: slice, value: Iterable[T]) -> None: ...
    
    @final
    def __setitem__(self, index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
        SetItems(self, index, value)
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        RemoveItems(self, index)