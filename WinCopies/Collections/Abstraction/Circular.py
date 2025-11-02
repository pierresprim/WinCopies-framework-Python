from collections.abc import Iterable, Sequence as SequenceBase
from typing import overload, final, SupportsIndex

from WinCopies.Collections.Circular import ICircularTuple, ICircularEquatableTuple, ICircularArray, ICircularList
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IArray, IList, TupleBase, ArrayBase, Sequence, MutableSequence, Tuple, EquatableTuple, ReversedListBase
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Typing import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation, IEquatableItem
from WinCopies.Typing.Delegate import IFunction, Method, ValueFunctionUpdater

class CircularBase[TItem, TList](TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], GenericConstraint[TList, ICircularTuple[TItem]]):
    def __init__(self, items: TList):
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
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]:
        return GetItems(self, index)

class CircularTuple[T](CircularBase[T, ICircularTuple[T]], Tuple[T], IGenericConstraintImplementation[ICircularTuple[T]]):
    def __init__(self, items: ICircularTuple[T]):
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetInnerContainer().SliceAt(key)
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, ICircularEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[ICircularEquatableTuple[T]]):
    def __init__(self, items: ICircularEquatableTuple[T]):
        super().__init__(items)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(key)
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], ArrayBase[TItem, TList], ICircularArray[TItem], GenericSpecializedConstraint[TList, ICircularTuple[TItem], ICircularArray[TItem]]):
    def __init__(self, items: TList):
        super().__init__(items)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(key, value)
class CircularArray[T](CircularArrayBase[T, ICircularArray[T]], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularArray[T]]):
    @final
    class __Reversed(ArrayBase[T, ICircularArray[T]].Reversed, ICircularArray[T], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularArray[T]]):
        def __init__(self, items: ICircularArray[T]):
            super().__init__(items)
        
        def GetStart(self) -> int:
            return self._GetContainer().GetStart()
    
    @final
    class __Updater(ValueFunctionUpdater[ICircularArray[T]]):
        def __init__(self, array: ICircularArray[T], updater: Method[IFunction[ICircularArray[T]]]):
            super().__init__(updater)

            self.__array: ICircularArray[T] = array
        
        def _GetValue(self) -> ICircularArray[T]:
            return CircularArray[T].__Reversed(self.__array)
    
    def __init__(self, items: ICircularArray[T]):
        super().__init__(items)
    
    @final
    def _GetUpdater(self, func: Method[IFunction[ICircularArray[T]]]) -> IFunction[ICircularArray[T]]:
        return CircularArray[T].__Updater(self, func)
    
    @final
    def AsReversed(self) -> IArray[T]:
        return self._AsReversed()
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._GetContainer().SliceAt(key)
class CircularList[T](CircularArrayBase[T, ICircularList[T]], MutableSequence[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ICircularTuple[T], ICircularList[T]]):
    @final
    class __Reversed(ReversedListBase[T, ICircularList[T]], ICircularList[T], IGenericSpecializedConstraintImplementation[ITuple[T], ICircularList[T]]):
        def __init__(self, items: ICircularList[T]):
            super().__init__(items)
        
        def GetStart(self) -> int:
            return self._GetContainer().GetStart()
        
        def _GetContainerAsList(self, container: ICircularList[T]) -> IList[T]:
            return container
    
    @final
    class __Updater(ValueFunctionUpdater[ICircularList[T]]):
        def __init__(self, array: ICircularList[T], updater: Method[IFunction[ICircularList[T]]]):
            super().__init__(updater)

            self.__array: ICircularList[T] = array
        
        def _GetValue(self) -> ICircularList[T]:
            return CircularList[T].__Reversed(self.__array)
    
    def __init__(self, items: ICircularList[T]):
        super().__init__(items)
    
    @final
    def _GetUpdater(self, func: Method[IFunction[ICircularList[T]]]) -> IFunction[ICircularList[T]]:
        return CircularList[T].__Updater(self, func)
    
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
    def __delitem__(self, index: int|slice):
        RemoveItems(self, index)