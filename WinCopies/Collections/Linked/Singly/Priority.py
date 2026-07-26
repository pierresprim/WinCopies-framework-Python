from __future__ import annotations

from abc import abstractmethod
from typing import Iterable, final

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Abstraction.Collection import ArrayList, SortedList
from WinCopies.Collections.Core import IArray
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Linked.Singly import IList, IQueue, IStack, IReadOnlyQueue, IReadOnlyStack, Queue, Stack, ReadOnlyQueueUpdater, ReadOnlyStackUpdater
from WinCopies.Typing import INullable, GetNullValue
from WinCopies.Typing.Delegate import IFunction, Converter
from WinCopies.Typing.Enum import IntEnum
from WinCopies.Typing.Generic import GenericConstraint

class PriorityLevel(IntEnum):
    Lowest = -4
    VeryLow = -3
    Lower = -2
    Low = -1
    Normal = 0
    High = 1
    Higher = 2
    VeryHigh = 3
    Highest = 4

class IPriorityListDictionary[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        ...

    @abstractmethod
    def TryGetItems(self, index: int) -> IList[T]|None:
        ...

    @abstractmethod
    def TryAppend(self, index: int) -> IList[T]|None:
        ...
    
    @abstractmethod
    def TryPeek(self) -> INullable[T]:
        ...

    @abstractmethod
    def TryPop(self) -> INullable[T]:
        ...

    @abstractmethod
    def Clear(self) -> None:
        ...
class PriorityListDictionaryAbstract[T](Abstract, IPriorityListDictionary[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__indices: ISortedList[int] = SortedList[int]()
    
    @abstractmethod
    def _ClearArray(self) -> None:
        ...

    @abstractmethod
    def _GetItems(self) -> IArray[IList[T]]:
        ...
    @final
    def _GetIndices(self) -> ISortedList[int]:
        return self.__indices
    
    @final
    def __TryPeek(self) -> int|None:
        return self._GetIndices().TryGetLastItem().TryGetValue()
    
    @final
    def __GetAt(self, index: int) -> IList[T]:
        return self._GetItems().GetAt(index)
    
    @final
    def __TryGet(self, converter: Converter[int, INullable[T]]) -> INullable[T]:
        def removeAt(index: int) -> None: self._GetIndices().Remove(index)
        
        index: int|None = self.__TryPeek()
        
        if index is None: return GetNullValue()
        
        result: INullable[T] = converter(index)

        if result.HasValue(): return result
        
        removeAt(index)

        while (index := self.__TryPeek()) is not None:
            if (result := converter(index)).HasValue(): return result
            
            removeAt(index)
        
        return GetNullValue()

    @final
    def IsEmpty(self) -> bool: return self._GetIndices().IsEmpty()
    
    @final
    def TryGetItems(self, index: int) -> IList[T]|None: return self._GetItems().TryGetValue(index).TryGetValue() if self._GetIndices().Contains(index) else None

    @final
    def TryAppend(self, index: int) -> IList[T]|None:
        items: IArray[IList[T]] = self._GetItems()

        if items.ValidateIndex(index):
            indices: ISortedList[int] = self._GetIndices()

            if not indices.Contains(index): indices.Add(index)

            return self._GetItems().GetAt(index)
        
        return None
    
    @final
    def TryPeek(self) -> INullable[T]: return self.__TryGet(lambda index: self.__GetAt(index).TryPeek())
    
    @final
    def TryPop(self) -> INullable[T]: return self.__TryGet(lambda index: self.__GetAt(index).TryPop())
    
    @final
    def Clear(self) -> None:
        self._GetIndices().Clear()
        self._ClearArray()
class PriorityListDictionaryBase[TItem, TArray](PriorityListDictionaryAbstract[TItem], GenericConstraint[TArray, IArray[IList[TItem]]]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: TArray = self._CreateArray()
    
    @abstractmethod
    def _CreateArray(self) -> TArray:
        ...
    @final
    def _ClearArray(self) -> None:
        self.__items = self._CreateArray()

    @final
    def _GetContainer(self) -> TArray: return self.__items

    @final
    def _GetItems(self) -> IArray[IList[TItem]]:
        return self._GetInnerContainer()
class PriorityListDictionary[T](PriorityListDictionaryBase[T, IArray[IList[T]]]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _AsContainer(self, container: IArray[IList[T]]) -> IArray[IList[T]]: return container

class _PriorityListDictionary[T](PriorityListDictionary[T]):
    def __init__(self, func: IFunction[IList[T]]) -> None:
        super().__init__()

        self.__func: IFunction[IList[T]] = func
    
    @final
    def _CreateArray(self) -> IArray[IList[T]]: return ArrayList[IList[T]](len(PriorityLevel), self.__func)

class IPriorityItemList[TItem, TLevel](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsEmpty(self) -> bool:
        ...
    
    @abstractmethod
    def TryAppend(self, level: TLevel) -> IList[TItem]|None:
        ...

    @abstractmethod
    def TryPeek(self) -> INullable[TItem]:
        ...
    @abstractmethod
    def TryPop(self) -> INullable[TItem]:
        ...
    
    @abstractmethod
    def Clear(self) -> None:
        ...
class PriorityItemListBase[TItem, TLevel](Abstract, IPriorityItemList[TItem, TLevel]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IPriorityListDictionary[TItem] = self._CreateDictionary()
    
    @abstractmethod
    def _CreateDictionary(self) -> IPriorityListDictionary[TItem]:
        ...
    
    @final
    def _GetItems(self) -> IPriorityListDictionary[TItem]:
        return self.__items
    
    @abstractmethod
    def _Convert(self, level: TLevel) -> int:
        ...

    @final
    def _TryGetItemsAt(self, index: int) -> IList[TItem]|None:
        return self._GetItems().TryGetItems(index)
    
    @final
    def IsEmpty(self) -> bool: return self._GetItems().IsEmpty()

    @final
    def TryAppend(self, level: TLevel) -> IList[TItem]|None:
        index: int = self._Convert(level)

        items: IList[TItem]|None = self._TryGetItemsAt(index)

        if items is None: items = self._GetItems().TryAppend(index)

        return items
    
    @final
    def TryPeek(self) -> INullable[TItem]: return self._GetItems().TryPeek()
    
    @final
    def TryPop(self) -> INullable[TItem]: return self._GetItems().TryPop()
    
    @final
    def Clear(self) -> None: self._GetItems().Clear()
class PriorityItemList[T](PriorityItemListBase[T, PriorityLevel]):
    @final
    class _Function[_T](Abstract, IFunction[IList[_T]]):
        def __init__(self, items: PriorityItemList[_T]) -> None:
            super().__init__()

            self.__items: PriorityItemList[_T] = items
        
        def GetValue(self) -> IList[_T]: return self.__items._CreateList()
    
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateDictionary(self) -> IPriorityListDictionary[T]:
        return _PriorityListDictionary[T](PriorityItemList[T]._Function(self))
    @abstractmethod
    def _CreateList(self) -> IList[T]:
        ...
    
    @final
    def _Convert(self, level: PriorityLevel) -> int: return level.value - PriorityLevel.Lowest.value

class PriorityItemQueue[T](PriorityItemList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateList(self) -> IList[T]: return Queue[T]()
class PriorityItemStack[T](PriorityItemList[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _CreateList(self) -> IList[T]: return Stack[T]()

class IPriorityList[TItem, TLevel](IList[TItem]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetNormalLevel(self) -> TLevel:
        ...
    
    @abstractmethod
    def TryPushAt(self, level: TLevel, value: TItem) -> bool:
        ...

    @final
    def PushItemsAt(self, level: TLevel, items: Iterable[TItem]) -> bool:
        for item in items:
            if not self.TryPushAt(level, item): return False
        
        return True
    @final
    def TryPushItemsAt(self, level: TLevel, items: Iterable[TItem]|None) -> bool: return False if items is None else self.PushItemsAt(level, items)
    
    @final
    def PushValuesAt(self, level: TLevel, *values: TItem) -> None: self.PushItemsAt(level, values)
class PriorityListBase[TItem, TLevel](Abstract, IPriorityList[TItem, TLevel]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IPriorityItemList[TItem, TLevel] = self._CreateDictionary()

    @abstractmethod
    def _CreateDictionary(self) -> IPriorityItemList[TItem, TLevel]:
        ...

    @final
    def _GetItems(self) -> IPriorityItemList[TItem, TLevel]:
        return self.__items
    
    @final
    def _TryGetAt(self, level: TLevel) -> IList[TItem]|None:
        return self._GetItems().TryAppend(level)
    
    @final
    def IsEmpty(self) -> bool: return self._GetItems().IsEmpty()
    
    @final
    def TryPeek(self) -> INullable[TItem]: return self._GetItems().TryPeek()
    
    @final
    def TryPushAt(self, level: TLevel, value: TItem) -> bool:
        items: IList[TItem]|None = self._TryGetAt(level)
        
        if items is None: return False
        
        items.Push(value)

        return True
    @final
    def Push(self, value: TItem) -> None: self.TryPushAt(self.GetNormalLevel(), value)
    
    @final
    def TryPop(self) -> INullable[TItem]: return self._GetItems().TryPop()
    
    @final
    def Clear(self) -> None: self._GetItems().Clear()
class PriorityList[T](PriorityListBase[T, PriorityLevel]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def GetNormalLevel(self) -> PriorityLevel: return PriorityLevel.Normal

class PriorityQueue[T](PriorityList[T], IQueue[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyQueue[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyQueue[T]] = ReadOnlyQueueUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _CreateDictionary(self) -> IPriorityItemList[T, PriorityLevel]: return PriorityItemQueue[T]()
    
    @final
    def AsReadOnly(self) -> IReadOnlyQueue[T]: return self.__readOnly.GetValue()
class PriorityStack[T](PriorityList[T], IStack[T]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyStack[T]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyStack[T]] = ReadOnlyStackUpdater[T](self, update) # type: ignore[no-redef]
    
    @final
    def _CreateDictionary(self) -> IPriorityItemList[T, PriorityLevel]: return PriorityItemStack[T]()
    
    @final
    def AsReadOnly(self) -> IReadOnlyStack[T]: return self.__readOnly.GetValue()