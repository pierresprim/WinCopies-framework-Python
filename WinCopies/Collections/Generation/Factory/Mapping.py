from __future__ import annotations

from abc import abstractmethod
from typing import final
from weakref import ReferenceType, ref

from WinCopies import IDisposableBase, Abstract
from WinCopies.Collections.Abstraction.Collection.Mapping import CreateDictionary
from WinCopies.Collections.Extensions import IDictionary
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Generation.Factory import ObjectFactoryBase, CompositeRemovable
from WinCopies.Collections.Generation.Factory.Keyable import IKeyableObjectFactoryBase, IKeyableObjectFactory
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode
from WinCopies.Typing import INullable, GetNullableValue
from WinCopies.Typing.Comparison import HashableProtocol
from WinCopies.Typing.Object import WeakReference

@final
class _KeyedNode[TKey: HashableProtocol, TValue: IDisposableBase](Abstract, IRemovable):
    def __init__(self, key: TKey, items: IDictionary[TKey, ReferenceType[TValue]]) -> None:
        super().__init__()

        self.__key: TKey = key
        self.__items: IDictionary[TKey, ReferenceType[TValue]] = items
    
    def Remove(self) -> None: self.__items.TryRemove(self.__key)

class KeyedObjectFactoryBase[TKey: HashableProtocol, TIn, TOut: IDisposableBase](ObjectFactoryBase[TIn, TOut], IKeyableObjectFactoryBase[TKey, TIn, TOut]):
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
    
    def _GetRemovable(self, obj: TOut, node: IDoublyLinkedNode[WeakReference[TOut]]) -> IRemovable:
        items: IDictionary[TKey, ReferenceType[TOut]] = self._GetKeyedItems()
        key: TKey = self._GetKey(obj)
        
        try: items.Add(key, ref(obj))
        
        except KeyError:
            node.Remove()

            raise
        
        return CompositeRemovable[TOut](node, _KeyedNode[TKey, TOut](key, items))
    
    @final
    def IsEmpty(self) -> bool: return self._GetKeyedItems().IsEmpty()
    
    @final
    def TryGetValue(self, key: TKey) -> INullable[TOut]: return GetNullableValue(self.__TryGetValue(key))
    
    @final
    def ContainsKey(self, key: TKey) -> bool: return self.__TryGetValue(key) is not None
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()
        
        self._GetKeyedItems().Clear()

class KeyedObjectFactory[TKey: HashableProtocol, TValue](KeyedObjectFactoryBase[TKey, TValue, IDisposableBase]):
    def __init__(self) -> None: super().__init__()
class KeyedDisposableObjectFactory[TKey: HashableProtocol, TValue: IDisposableBase](KeyedObjectFactoryBase[TKey, TValue, TValue], IKeyableObjectFactory[TKey, TValue]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue: return item