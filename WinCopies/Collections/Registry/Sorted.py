from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence
from typing import final

from WinCopies.Collections.Core import IReadOnlyCollection, IClearable, ICountable, Countable
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Iteration import Include
from WinCopies.Collections.Registry.Core import ObjectRegistryBase
from WinCopies.Collections.Registry.Kernel import CompositeNode
from WinCopies.Collections.Registry.Keyable import IKeyableObjectRegistryBase, IKeyableObjectRegistry, INode, Node, GetKey, ExtractKey
from WinCopies.Collections.Util import TryBisectWithKey, Insort, ThrowValueNotFoundError
from WinCopies.Comparison import CompareTo
from WinCopies.Typing import INullable, TryGetNullable, GetNullableValue
from WinCopies.Typing.Comparison import IHashableComparableItem
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Pairing import DualValueBool
from WinCopies.Typing.Protocols import SupportsEqualityAndRichComparison

class ISortedNode[TKey: SupportsEqualityAndRichComparison, TValue](INode[TKey, TValue], IHashableComparableItem[TKey]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> TKey: return self.GetKey()
@final
class _SortedNode[TKey: SupportsEqualityAndRichComparison, TValue: IInvalidatable](Node[TKey, TValue], ISortedNode[TKey, TValue], IRemovable):
    def __init__(self, key: TKey, obj: TValue, items: ISortedList[TKey, TValue]) -> None:
        super().__init__(key, obj)

        self.__items: ISortedList[TKey, TValue] = items
    
    def _CompareTo(self, item: _SortedNode[TKey, TValue]|TKey|object) -> bool|None:
        value: object = ExtractKey(item)

        if isinstance(value, SupportsEqualityAndRichComparison): return CompareTo(self.GetKey(), value)

        raise NotImplementedError()
    
    def Remove(self) -> None:
        # Removed by identity, so that the node of another object of the same key is kept.
        self.__items.TryRemoveNode(self)

class ISortedList[TKey: SupportsEqualityAndRichComparison, TValue](IReadOnlyCollection, IClearable, ICountable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def TryBisect(self, key: TKey, right: bool = False) -> DualValueBool[int]:
        ...
    
    @abstractmethod
    def ContainsKey(self, key: TKey) -> bool:
        ...
    
    @abstractmethod
    def TryGetNode(self, key: TKey) -> ISortedNode[TKey, TValue]|None:
        ...
    
    @abstractmethod
    def Add(self, item: ISortedNode[TKey, TValue]) -> None:
        ...
    
    @abstractmethod
    def Remove(self, key: TKey) -> None:
        ...
    @abstractmethod
    def TryRemove(self, key: TKey) -> bool:
        ...
    @abstractmethod
    def TryRemoveNode(self, node: ISortedNode[TKey, TValue]) -> bool:
        """
        Removes a node by identity, so that a node of the same key is never removed in its place.

        Args:
            node: The node to remove.

        Returns:
            Whether the node was found, and thus removed."""
        ...
    
    @abstractmethod
    def Purge(self) -> None:
        """Removes the nodes whose object is dead."""
        ...
class SortedList[TKey: SupportsEqualityAndRichComparison, TValue](Countable, ISortedList[TKey, TValue]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: MutableSequence[ISortedNode[TKey, TValue]] = list[ISortedNode[TKey, TValue]]()
    
    @final
    def GetCount(self) -> int: return len(self.__items)
    
    @final
    def IsEmpty(self) -> bool: return self.GetCount() < 1

    @final
    def TryBisect(self, key: TKey, right: bool = False) -> DualValueBool[int]:
        index: DualValueBool[int]|None = TryBisectWithKey(self.__items, key, GetKey, right)

        assert index is not None

        return index
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self.TryBisect(key).GetValue()
    
    @final
    def TryGetNode(self, key: TKey) -> ISortedNode[TKey, TValue]|None:
        index: DualValueBool[int] = self.TryBisect(key)

        return self.__items[index.GetKey()] if index.GetValue() else None

    @final
    def Add(self, item: ISortedNode[TKey, TValue]) -> None: Insort(self.__items, item, True)
    
    @final
    def TryRemove(self, key: TKey) -> bool:
        index: DualValueBool[int] = self.TryBisect(key)

        if index.GetValue():
            self.__items.pop(index.GetKey())

            return True

        return False
    @final
    def Remove(self, key: TKey) -> None:
        if not self.TryRemove(key): ThrowValueNotFoundError(key)
    @final
    def TryRemoveNode(self, node: ISortedNode[TKey, TValue]) -> bool:
        items: MutableSequence[ISortedNode[TKey, TValue]] = self.__items

        # The bisection costs even on an empty list, and the index is empty while its registry invalidates its objects.
        if len(items) < 1: return False

        key: TKey = node.GetKey()
        index: int = self.TryBisect(key).GetKey()
        item: ISortedNode[TKey, TValue]

        # The nodes of the same key follow the first one, so that the node is looked for among them only.
        while index < len(items) and (item := items[index]).GetKey() == key:
            if item is node:
                items.pop(index)

                return True
            
            index += 1
        
        return False
    
    @final
    def Purge(self) -> None:
        self.__items[:] = tuple(Include(self.__items, lambda node: node.TryGetValue() is not None))

    @final
    def Clear(self) -> None: return self.__items.clear()

class ISortedObjectRegistryBase[TKey, TIn, TOut](IKeyableObjectRegistryBase[TKey, TIn, TOut]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryBisect(self, key: TKey, right: bool = False) -> DualValueBool[int]:
        ...
    
    @abstractmethod
    def TryGetItem(self, key: TKey) -> INullable[TOut]|None:
        ...

class ISortedObjectRegistry[TKey, TValue](ISortedObjectRegistryBase[TKey, TValue, IInvalidatable]):
    def __init__(self) -> None: super().__init__()
class ISortedDisposableObjectRegistry[TKey, TValue](ISortedObjectRegistryBase[TKey, TValue, TValue], IKeyableObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class SortedObjectRegistryBase[TKey: SupportsEqualityAndRichComparison, TIn, TOut: IInvalidatable](ObjectRegistryBase[TIn, TOut], ISortedObjectRegistryBase[TKey, TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: ISortedList[TKey, TOut] = SortedList[TKey, TOut]()
    
    @final
    def _GetSortedItems(self) -> ISortedList[TKey, TOut]:
        return self.__items
    
    @abstractmethod
    def _GetKey(self, item: TOut) -> TKey:
        ...
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> INodeBase:
        items: ISortedList[TKey, TOut] = self._GetSortedItems()
        sortedNode: _SortedNode[TKey, TOut] = _SortedNode[TKey, TOut](self._GetKey(obj), obj, items)

        items.Add(sortedNode)

        return CompositeNode(node, sortedNode)
    
    def _Purge(self) -> int:
        count: int = super()._Purge()
        items: ISortedList[TKey, TOut] = self._GetSortedItems()

        # Each live object has one entry in the list and one in the index, so that the index holds the entries of dead objects only if it holds more entries than the list kept.
        if items.GetCount() > count: items.Purge()

        return count
    
    @final
    def IsEmpty(self) -> bool: return self._GetSortedItems().IsEmpty()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self._GetSortedItems().ContainsKey(key)
    
    @final
    def TryGetItem(self, key: TKey) -> INullable[TOut]|None:
        items: ISortedList[TKey, TOut] = self._GetSortedItems()
        node: ISortedNode[TKey, TOut]|None

        # The node of a dead object stays in the index until it is found or purged, so the dead nodes found first for the key are dropped here.
        while (node := items.TryGetNode(key)) is not None:
            value: TOut|None = node.TryGetValue()

            if value is not None: return GetNullableValue(value)

            items.TryRemoveNode(node)
        
        return None
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]:
        return TryGetNullable(self.TryGetItem(key))
    
    @final
    def TryBisect(self, key: TKey, right: bool = False) -> DualValueBool[int]: return self._GetSortedItems().TryBisect(key, right)
    
    def InvalidateObjects(self) -> None:
        # The index is emptied first, so that the objects that the invalidation disposes find no node to remove, and again after, for the objects registered during the invalidation.
        self._GetSortedItems().Clear()

        try: super().InvalidateObjects()
        finally: self._GetSortedItems().Clear()
class SortedObjectRegistry[TKey: SupportsEqualityAndRichComparison, TValue](SortedObjectRegistryBase[TKey, TValue, IInvalidatable], ISortedObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class SortedDisposableObjectRegistry[TKey: SupportsEqualityAndRichComparison, TValue: IInvalidatable](SortedObjectRegistryBase[TKey, TValue, TValue], ISortedDisposableObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item