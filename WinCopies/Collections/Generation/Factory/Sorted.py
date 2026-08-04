from __future__ import annotations

from abc import abstractmethod
from bisect import bisect_left, bisect_right, insort_right
from collections.abc import MutableSequence
from typing import final

from WinCopies import IDisposableBase
from WinCopies.Collections.Core import IReadOnlyCollection, IClearable, Countable
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Factory.Core import ObjectFactoryBase, CompositeRemovable
from WinCopies.Collections.Generation.Factory.Keyable import IKeyableObjectFactoryBase, IKeyableObjectFactory, INode, Node, GetKey, ExtractKey
from WinCopies.Collections.Util import TryGetAt
from WinCopies.Typing import INullable, GetNullableValue
from WinCopies.Typing.Comparison import ComparableProtocol, IHashableComparableItem, CompareTo

class ISortedNode[TKey: ComparableProtocol, TValue](INode[TKey, TValue], IHashableComparableItem[TKey]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> TKey: return self.GetKey()
@final
class _SortedNode[TKey: ComparableProtocol, TValue: IDisposableBase](Node[TKey, TValue], ISortedNode[TKey, TValue], IRemovable):
    def __init__(self, key: TKey, obj: TValue, items: ISortedList[TKey, TValue]) -> None:
        super().__init__(key, obj)

        self.__items: ISortedList[TKey, TValue] = items
    
    def _CompareTo(self, item: _SortedNode[TKey, TValue]|TKey|object) -> bool|None: return CompareTo(self.GetKey(), ExtractKey(item))
    
    def Remove(self) -> None:
        items: ISortedList[TKey, TValue] = self.__items

        items.Remove(self.GetKey())

class ISortedList[TKey: ComparableProtocol, TValue](IReadOnlyCollection, IClearable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def BisectLeft(self, key: TKey) -> int:
        ...
    @abstractmethod
    def BisectRight(self, key: TKey) -> int:
        ...
    
    @abstractmethod
    def TryGetValue(self, key: TKey) -> ISortedNode[TKey, TValue]|None:
        ...
    
    @abstractmethod
    def Add(self, item: ISortedNode[TKey, TValue]) -> None:
        ...
    @abstractmethod
    def Remove(self, key: TKey) -> None:
        ...
class SortedList[TKey: ComparableProtocol, TValue](Countable, ISortedList[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: MutableSequence[ISortedNode[TKey, TValue]] = list[ISortedNode[TKey, TValue]]()
    
    @final
    def GetCount(self) -> int: return len(self.__items)
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1
    
    @final
    def BisectLeft(self, key: TKey) -> int: return bisect_left(self.__items, key, key = GetKey)
    @final
    def BisectRight(self, key: TKey) -> int: return bisect_right(self.__items, key, key = GetKey)
    
    @final
    def TryGetValue(self, key: TKey) -> ISortedNode[TKey, TValue]|None: return TryGetAt(self.__items, self.BisectLeft(key))

    @final
    def Add(self, item: ISortedNode[TKey, TValue]) -> None: insort_right(self.__items, item)
    @final
    def Remove(self, key: TKey) -> None: self.__items.pop(self.BisectLeft(key))

    @final
    def Clear(self) -> None: return self.__items.clear()

class ISortedObjectFactoryBase[TKey, TIn, TOut](IKeyableObjectFactoryBase[TKey, TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def BisectLeft(self, key: TKey) -> int:
        ...
    @abstractmethod
    def BisectRight(self, key: TKey) -> int:
        ...
class ISortedObjectFactory[TKey, TValue](ISortedObjectFactoryBase[TKey, TValue, TValue], IKeyableObjectFactory[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class SortedObjectFactoryBase[TKey: ComparableProtocol, TIn, TOut: IDisposableBase](ObjectFactoryBase[TIn, TOut], ISortedObjectFactoryBase[TKey, TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: ISortedList[TKey, TOut] = SortedList[TKey, TOut]()
    
    @final
    def __TryGetNode(self, key: TKey) -> ISortedNode[TKey, TOut]|None:
        return self._GetSortedItems().TryGetValue(key)
    
    @final
    def _GetSortedItems(self) -> ISortedList[TKey, TOut]:
        return self.__items
    
    @abstractmethod
    def _GetKey(self, item: TOut) -> TKey:
        ...
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> IRemovable:
        items: ISortedList[TKey, TOut] = self._GetSortedItems()
        sortedNode: _SortedNode[TKey, TOut] = _SortedNode[TKey, TOut](self._GetKey(obj), obj, items)

        items.Add(sortedNode)

        return CompositeRemovable(node, sortedNode)
    
    @final
    def IsEmpty(self) -> bool: return self._GetSortedItems().IsEmpty()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        node: ISortedNode[TKey, TOut]|None = self.__TryGetNode(key)

        return node is not None and node.GetKey() == key
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]:
        node: ISortedNode[TKey, TOut]|None = self.__TryGetNode(key)
        
        return GetNullableValue(None if node is None else (node.TryGetValue() if node.GetKey() == key else None))
    
    @final
    def BisectLeft(self, key: TKey) -> int: return self._GetSortedItems().BisectLeft(key)
    @final
    def BisectRight(self, key: TKey) -> int: return self._GetSortedItems().BisectRight(key)
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()
        
        self._GetSortedItems().Clear()
class SortedObjectFactory[TKey: ComparableProtocol, TValue](SortedObjectFactoryBase[TKey, TValue, IDisposableBase]):
    def __init__(self) -> None: super().__init__()

class SortedDisposableObjectFactory[TKey: ComparableProtocol, TValue: IDisposableBase](SortedObjectFactoryBase[TKey, TValue, TValue], ISortedObjectFactory[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item