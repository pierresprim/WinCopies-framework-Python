from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IDisposableBase
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Factory import ObjectFactoryBase, CompositeRemovable
from WinCopies.Collections.Generation.Factory.Keyable import IKeyableObjectFactoryBase, IKeyableObjectFactory, INode, Node, GetKey, ExtractKey
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode
from WinCopies.Typing import INullable, GetNullableValue
from WinCopies.Typing.Comparison import IExtendedComparable, HashableComparableProtocol, CompareTo
from WinCopies.Typing.Object import WeakReference

class ISortedNode[TKey, TValue](INode[TKey, TValue], IExtendedComparable['ISortedNode[TKey, TValue]|TKey']):
    def __init__(self) -> None:
        super().__init__()

@final
class _SortedNode[TKey: HashableComparableProtocol, TValue: IDisposableBase](Node[TKey, TValue], ISortedNode[TKey, TValue], IRemovable):
    def __init__(self, key: TKey, obj: TValue, items: ISortedList[ISortedNode[TKey, TValue]]) -> None:
        super().__init__(key, obj)

        self.__items: ISortedList[ISortedNode[TKey, TValue]] = items
    
    def CompareTo(self, item: _SortedNode[TKey, TValue]|TKey|object) -> bool|None:
        return CompareTo(self.GetKey(), ExtractKey(item))
    
    def Remove(self) -> None:
        items: ISortedList[ISortedNode[TKey, TValue]] = self.__items

        items.RemoveAt(items.BisectLeft(self.GetKey(), GetKey))

class SortedObjectFactoryBase[TKey: HashableComparableProtocol, TIn, TOut: IDisposableBase](ObjectFactoryBase[TIn, TOut], IKeyableObjectFactoryBase[TKey, TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: ISortedList[ISortedNode[TKey, TOut]] = SortedList[ISortedNode[TKey, TOut]]()
    
    @final
    def __TryGetNode(self, key: TKey) -> ISortedNode[TKey, TOut]|None:
        items: ISortedList[ISortedNode[TKey, TOut]] = self._GetSortedItems()

        return items.TryGetValue(items.BisectLeft(key, GetKey)).TryGetValue()
    
    @final
    def _GetSortedItems(self) -> ISortedList[ISortedNode[TKey, TOut]]:
        return self.__items
    
    @abstractmethod
    def _GetKey(self, item: TOut) -> TKey:
        pass
    
    def _GetRemovable(self, obj: TOut, node: IDoublyLinkedNode[WeakReference[TOut]]) -> IRemovable:
        items: ISortedList[ISortedNode[TKey, TOut]] = self._GetSortedItems()
        sortedNode: _SortedNode[TKey, TOut] = _SortedNode[TKey, TOut](self._GetKey(obj), obj, items)

        items.Add(sortedNode)

        return CompositeRemovable[TOut](node, sortedNode)
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetSortedItems().IsEmpty()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        node: ISortedNode[TKey, TOut]|None = self.__TryGetNode(key)

        return node is not None and node.GetKey() == key
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]:
        node: ISortedNode[TKey, TOut]|None = self.__TryGetNode(key)
        
        return GetNullableValue(None if node is None else (node.TryGetValue() if node.GetKey() == key else None))
    
    @final
    def BisectLeft(self, key: TKey) -> int:
        return self._GetSortedItems().BisectLeft(key, GetKey)
    @final
    def BisectRight(self, key: TKey) -> int:
        return self._GetSortedItems().BisectRight(key, GetKey)
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()
        
        self._GetSortedItems().Clear()
class SortedObjectFactory[TKey: HashableComparableProtocol, TValue](SortedObjectFactoryBase[TKey, TValue, IDisposableBase]):
    def __init__(self) -> None:
        super().__init__()

class SortedDisposableObjectFactory[TKey: HashableComparableProtocol, TValue: IDisposableBase](SortedObjectFactoryBase[TKey, TValue, TValue], IKeyableObjectFactory[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue:
        return item