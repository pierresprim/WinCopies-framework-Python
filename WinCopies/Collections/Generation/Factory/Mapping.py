from __future__ import annotations

from abc import abstractmethod
from typing import final
from weakref import ReferenceType, ref

from WinCopies import Abstract
from WinCopies.Collections.Abstraction.Mapping import CreateDictionary
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Generation.Factory.Core import ObjectRegistryBase, CompositeRemovable
from WinCopies.Collections.Generation.Factory.Keyable import IKeyableObjectRegistryBase, IKeyableObjectRegistry
from WinCopies.Typing import INullable, GetNullableValue
from WinCopies.Typing.Comparison import HashableProtocol
from WinCopies.Typing.Discard import IInvalidatable

@final
class _KeyedNode[TKey: HashableProtocol, TValue: IInvalidatable](Abstract, IRemovable):
    def __init__(self, key: TKey, items: IDictionary[TKey, ReferenceType[TValue]]) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__items: IDictionary[TKey, ReferenceType[TValue]] = items
    
    def Remove(self) -> None: self.__items.TryRemove(self.__key)

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
    
    def _GetRemovable(self, obj: TOut, node: INode) -> IRemovable:
        items: IDictionary[TKey, ReferenceType[TOut]] = self._GetKeyedItems()
        key: TKey = self._GetKey(obj)
        
        try: items.Add(key, ref(obj))
        
        except KeyError:
            node.Remove()

            raise
        
        return CompositeRemovable(node, _KeyedNode[TKey, TOut](key, items))
    
    @final
    def IsEmpty(self) -> bool: return self._GetKeyedItems().IsEmpty()
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]: return GetNullableValue(self.__TryGetValue(key))
    
    @final
    def ContainsKey(self, key: TKey) -> bool: return self.__TryGetValue(key) is not None
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()
        
        self._GetKeyedItems().Clear()

class KeyedObjectRegistry[TKey: HashableProtocol, TValue](KeyedObjectRegistryBase[TKey, TValue, IInvalidatable]):
    def __init__(self) -> None: super().__init__()
class KeyedDisposableObjectRegistry[TKey: HashableProtocol, TValue: IInvalidatable](KeyedObjectRegistryBase[TKey, TValue, TValue], IKeyableObjectRegistry[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item