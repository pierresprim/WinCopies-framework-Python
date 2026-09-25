from __future__ import annotations

from abc import abstractmethod
from collections.abc import MutableSequence
from typing import final

from WinCopies.Collections.Core import IReadOnlyCollection, IClearable, Countable
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Registry.Core import ObjectRegistryBase
from WinCopies.Collections.Registry.Kernel import CompositeRemovable
from WinCopies.Collections.Registry.Keyable import IKeyableObjectRegistryBase, IKeyableObjectRegistry, INode, Node, GetKey, ExtractKey
from WinCopies.Collections.Util import TryBisectWithKey, Insort
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
        items: ISortedList[TKey, TValue] = self.__items

        items.TryRemove(self.GetKey())

class ISortedList[TKey: SupportsEqualityAndRichComparison, TValue](IReadOnlyCollection, IClearable):
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
        if not self.TryRemove(key): raise ValueError(key)

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
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> IRemovable:
        items: ISortedList[TKey, TOut] = self._GetSortedItems()
        sortedNode: _SortedNode[TKey, TOut] = _SortedNode[TKey, TOut](self._GetKey(obj), obj, items)

        items.Add(sortedNode)

        return CompositeRemovable(node, sortedNode)
    
    @final
    def IsEmpty(self) -> bool: return self._GetSortedItems().IsEmpty()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        return self._GetSortedItems().ContainsKey(key)
    
    @final
    def TryGetItem(self, key: TKey) -> INullable[TOut]|None:
        node: ISortedNode[TKey, TOut]|None = self._GetSortedItems().TryGetNode(key)
        
        return None if node is None else GetNullableValue(node.TryGetValue())
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]:
        return TryGetNullable(self.TryGetItem(key))
    
    @final
    def TryBisect(self, key: TKey, right: bool = False) -> DualValueBool[int]: return self._GetSortedItems().TryBisect(key, right)
    
    def InvalidateObjects(self) -> None:
        try: super().InvalidateObjects()
        finally: self._GetSortedItems().Clear()
class SortedObjectRegistry[TKey: SupportsEqualityAndRichComparison, TValue](SortedObjectRegistryBase[TKey, TValue, IInvalidatable], ISortedObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()

class SortedDisposableObjectRegistry[TKey: SupportsEqualityAndRichComparison, TValue: IInvalidatable](SortedObjectRegistryBase[TKey, TValue, TValue], ISortedDisposableObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item