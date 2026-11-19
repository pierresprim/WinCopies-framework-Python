from __future__ import annotations

from abc import abstractmethod
from typing import final
from weakref import ReferenceType, ref

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Mapping import CreateDictionary
from WinCopies.Collections.Extensions.Mapping import IDictionary
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Iteration import Include
from WinCopies.Collections.Registry.Core import ObjectRegistryBase
from WinCopies.Collections.Registry.Kernel import CompositeNode
from WinCopies.Collections.Registry.Keyable import IKeyableObjectRegistryBase, IKeyableObjectRegistry
from WinCopies.Typing import INullable, GetNullableValue
from WinCopies.Typing.Comparison import HashableProtocol
from WinCopies.Typing.Discard import IInvalidatable

@final
class _KeyedNode[TKey: HashableProtocol, TValue: IInvalidatable](Abstract, IRemovable):
    def __init__(self, key: TKey, reference: ReferenceType[TValue], items: IDictionary[TKey, ReferenceType[TValue]]) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__reference: ReferenceType[TValue] = reference
        self.__items: IDictionary[TKey, ReferenceType[TValue]] = items
    
    def Remove(self) -> None:
        items: IDictionary[TKey, ReferenceType[TValue]] = self.__items
        key: TKey = self.__key

        # Removed by identity, so that the entry of another object registered since under the same key is kept.
        if items.TryGetValue(key).TryGetValue() is self.__reference: items.TryRemove(key)

class KeyedObjectRegistryBase[TKey: HashableProtocol, TIn, TOut: IInvalidatable](ObjectRegistryBase[TIn, TOut], IKeyableObjectRegistryBase[TKey, TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IDictionary[TKey, ReferenceType[TOut]] = CreateDictionary()
    
    @final
    def __TryGetValue(self, key: TKey) -> TOut|None:
        weakRefNullable: ReferenceType[TOut]|None = self._GetKeyedItems().TryGetValue(key).TryGetValue()
        
        if weakRefNullable is None: return None
        
        value: TOut|None = weakRefNullable()
        
        if value is None:
            self._GetKeyedItems().TryRemove(key)

            return None
        
        return value
    
    @final
    def _GetKeyedItems(self) -> IDictionary[TKey, ReferenceType[TOut]]:
        return self.__items
    
    @abstractmethod
    def _GetKey(self, item: TOut) -> TKey:
        pass
    
    def _GetRemovable(self, obj: TOut, node: INode) -> INode:
        items: IDictionary[TKey, ReferenceType[TOut]] = self._GetKeyedItems()
        key: TKey = self._GetKey(obj)
        reference: ReferenceType[TOut] = ref(obj)
        
        try: items.Add(key, reference)
        
        except KeyError:
            node.Remove()

            raise
        
        return CompositeNode(node, _KeyedNode[TKey, TOut](key, reference, items))
    
    def _Purge(self) -> int:
        def isDead(key: TKey) -> bool:
            reference: ReferenceType[TOut]|None = items.TryGetValue(key).TryGetValue()

            return reference is not None and reference() is None
        
        count: int = super()._Purge()
        items: IDictionary[TKey, ReferenceType[TOut]] = self._GetKeyedItems()

        # Each live object has one entry in the list and one in the dictionary, so that the dictionary holds the entries of dead objects only if it holds more entries than the list kept.
        if items.GetCount() > count:
            # The keys are gathered before any removal, since the dictionary cannot change while it is enumerated.
            for key in tuple(Include(items.GetKeys().AsIterable(), isDead)): items.TryRemove(key)

        return count
    
    @final
    def IsEmpty(self) -> bool: return self._GetKeyedItems().IsEmpty()
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]: return GetNullableValue(self.__TryGetValue(key))
    
    @final
    def ContainsKey(self, key: TKey) -> bool: return self.__TryGetValue(key) is not None
    
    def InvalidateObjects(self) -> None:
        # The dictionary is emptied first, so that the objects that the invalidation disposes find no entry to remove, and again after, for the objects registered during the invalidation.
        self._GetKeyedItems().Clear()

        try: super().InvalidateObjects()
        finally: self._GetKeyedItems().Clear()

class KeyedObjectRegistry[TKey: HashableProtocol, TValue](KeyedObjectRegistryBase[TKey, TValue, IInvalidatable]):
    def __init__(self) -> None: super().__init__()
class KeyedDisposableObjectRegistry[TKey: HashableProtocol, TValue: IInvalidatable](KeyedObjectRegistryBase[TKey, TValue, TValue], IKeyableObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item