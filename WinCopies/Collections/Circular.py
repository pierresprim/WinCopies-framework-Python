from abc import abstractmethod
from collections.abc import Iterable, Sequence as SequenceBase
from typing import final, overload, SupportsIndex

from WinCopies import IStringable
from WinCopies.Collections.Extensions import ITuple, IEquatableTuple, IHashableTuple, IArray, IList, Sequence, MutableSequence
from WinCopies.Collections.Extensions.Collection import TupleAbstract, TupleBase, ArrayBase, Tuple, EquatableTuple, HashableTuple, Array, List
from WinCopies.Collections.Range import GetItems, SetItems, RemoveItems
from WinCopies.Typing.Comparison import IEquatableItem
from WinCopies.Typing.Generic import GenericConstraint, GenericSpecializedConstraint, IGenericConstraintImplementation, IGenericSpecializedConstraintImplementation

class ICircularTuple[T](ITuple[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetStart(self) -> int:
        pass
    
    @final
    def GetCircularIndex(self, index: int) -> int:
        return self.GetIndex(index, self.GetStart())[0]
class ICircularEquatableTuple[T: IEquatableItem](ICircularTuple[T], IEquatableTuple[T]):
    def __init__(self) -> None:
        super().__init__()
class ICircularHashableTuple[T: IEquatableItem](ICircularTuple[T], IHashableTuple[T]):
    def __init__(self) -> None:
        super().__init__()
class ICircularArray[T](ICircularTuple[T], IArray[T]):
    def __init__(self) -> None:
        super().__init__()
class ICircularList[T](ICircularArray[T], IList[T]):
    def __init__(self) -> None:
        super().__init__()

class CircularAbstract[TItem, TList](TupleAbstract[TItem], ICircularTuple[TItem], IStringable, GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList, start: int) -> None:
        super().__init__()
        
        self.__list: TList = items
        self.__start: int = start % self.GetCount()
    
    @final
    def _GetContainer(self) -> TList:
        return self.__list
    
    @final
    def _GetAt(self, key: int) -> TItem:
        return self._GetInnerContainer().GetAt(self.GetCircularIndex(key))
    
    @final
    def _GetKey(self, key: slice) -> slice:
        def getIndex(index: int) -> int:
            return index if index == count else self.GetCircularIndex(index)
        
        count = self.GetCount()
        start, stop, step = key.indices(count)
        
        return slice(getIndex(start), getIndex(stop), step)
    
    @final
    def Contains(self, value: TItem|object) -> bool:
        return self._GetInnerContainer().Contains(value)
    
    @final
    def GetCount(self) -> int:
        return self._GetInnerContainer().GetCount()
    
    @final
    def GetStart(self) -> int:
        return self.__start
    @final
    def SetStart(self, start: int = 0) -> None:
        self.__start = start
    
    def ToString(self) -> str:
        return self._GetInnerContainer().ToString()
class CircularBase[TItem, TList](CircularAbstract[TItem, TList], TupleBase[TItem], Sequence[TItem], ICircularTuple[TItem], IStringable, GenericConstraint[TList, ITuple[TItem]]):
    def __init__(self, items: TList, start: int) -> None:
        super().__init__(items, start)
    
    @overload
    def __getitem__(self, index: SupportsIndex) -> TItem: ...
    @overload
    def __getitem__(self, index: slice) -> SequenceBase[TItem]: ...
    
    @final
    def __getitem__(self, index: SupportsIndex|slice) -> TItem|SequenceBase[TItem]:
        return GetItems(self, index)

class CircularTuple[T](CircularBase[T, ITuple[T]], Tuple[T], IGenericConstraintImplementation[ITuple[T]]):
    def __init__(self, items: ITuple[T], start: int) -> None:
        super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> ITuple[T]:
        return self._GetInnerContainer().SliceAt(self._GetKey(key))
class CircularEquatableTuple[T: IEquatableItem](CircularBase[T, IEquatableTuple[T]], EquatableTuple[T], ICircularEquatableTuple[T], IGenericConstraintImplementation[IEquatableTuple[T]]):
    def __init__(self, items: IEquatableTuple[T], start: int) -> None:
        super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> IEquatableTuple[T]:
        return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Equals(self, item: object) -> bool:
        return self is item
class CircularHashableTuple[T: IEquatableItem](CircularBase[T, IHashableTuple[T]], HashableTuple[T], ICircularHashableTuple[T], IGenericConstraintImplementation[IHashableTuple[T]]):
    def __init__(self, items: IHashableTuple[T], start: int) -> None:
        super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> IHashableTuple[T]:
        return self._GetContainer().SliceAt(self._GetKey(key))
    
    def Hash(self) -> int:
        return self._GetContainer().Hash()
    
    def Equals(self, item: object) -> bool:
        return self is item

class CircularArrayBase[TItem, TList](CircularBase[TItem, TList], GenericSpecializedConstraint[TList, ITuple[TItem], IArray[TItem]], ArrayBase[TItem, TList], ICircularArray[TItem]):
    def __init__(self, items: TList, start: int) -> None:
        super().__init__(items, start)
    
    @final
    def _SetAt(self, key: int, value: TItem) -> None:
        self._GetSpecializedContainer().SetAt(self.GetCircularIndex(key), value)
class CircularArray[T](CircularArrayBase[T, IArray[T]], Array[T], IGenericSpecializedConstraintImplementation[ITuple[T], IArray[T]]):
    def __init__(self, items: IArray[T], start: int) -> None:
        super().__init__(items, start)
    
    @final
    def SliceAt(self, key: slice) -> IArray[T]:
        return self._GetContainer().SliceAt(self._GetKey(key))
class CircularList[T](CircularAbstract[T, IList[T]], List[T], MutableSequence[T], ICircularList[T], IGenericSpecializedConstraintImplementation[ITuple[T], IList[T]]):
    def __init__(self, items: IList[T], start: int) -> None:
        super().__init__(items, start)
    
    @final
    def _GetIndexOrKey(self, index: SupportsIndex|slice) -> SupportsIndex|slice:
        return self.GetCircularIndex(int(index)) if isinstance(index, SupportsIndex) else self._GetKey(index)
    
    @final
    def _SetAt(self, key: int, value: T) -> None:
        return self._GetContainer().SetAt(self.GetCircularIndex(key), value)
    
    @final
    def SliceAt(self, key: slice) -> IList[T]:
        return self._GetContainer().SliceAt(self._GetKey(key))
    
    @final
    def Add(self, item: T) -> None:
        def tryAdd() -> bool:
            if index == self.GetLastIndex():
                self._GetContainer().Add(item)

                return True
            
            return False

        index: int = self.GetCircularIndex(self.GetLastIndex())

        if tryAdd():
            return
        
        index += 1

        if not tryAdd():
            self._GetContainer().Insert(index, item)
    
    @final
    def TryInsert(self, index: int, value: T) -> bool:
        return self.ValidateIndex(index) and self._GetContainer().TryInsert(self.GetCircularIndex(index), value)
    
    @final
    def TryRemoveAt(self, index: int) -> bool|None:
        return self._GetContainer().TryRemoveAt(self.GetCircularIndex(index))
    
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
        SetItems(self, self._GetIndexOrKey(index), value)
    
    @final
    def __delitem__(self, index: int|slice) -> None:
        RemoveItems(self, self._GetIndexOrKey(index))