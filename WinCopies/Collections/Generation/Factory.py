from __future__ import annotations

from abc import abstractmethod
from typing import final
from weakref import ref, ReferenceType

from WinCopies import IInterface, IDisposableBase, Abstract
from WinCopies.Collections.Abstraction.Collection import SortedList
from WinCopies.Collections.Extensions import ISortedList
from WinCopies.Collections.Generation import IRemovable, INode
from WinCopies.Collections.Linked.Doubly import IDoublyLinkedNode, IReadOnlyList, IList, List
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, GetNullable, GetNullValue, GetNullableValue
from WinCopies.Typing.Comparison import IExtendedHashableComparableValue, IExtendedComparable
from WinCopies.Typing.Delegate import Action, Method, Function, Converter as ConverterDelegate, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Object import IWeakReferenceRegister, WeakReference, CreateWeakReferenceRegister

class CompositeRemovable[T: IDisposableBase](Abstract, IRemovable):
    def __init__(self, node: IDoublyLinkedNode[WeakReference[T]], obj: IRemovable) -> None:
        def remove() -> None:
            self.__node.Remove()
            self.__obj.Remove()

            self.__remove = NoAction

        super().__init__()

        self.__node: IRemovable = node
        self.__obj: IRemovable = obj
        self.__remove: Action = remove # type: ignore[no-redef]
    
    def Remove(self) -> None:
        self.__remove()

@final
class _ReadOnlyList[T: IDisposableBase](Abstract, IReadOnlyList[T]):
    def __init__(self, items: IList[WeakReference[T]]) -> None:
        super().__init__()

        self.__items: IList[WeakReference[T]] = items
    
    def __TryGetValue(self, getNode: Function[IDoublyLinkedNode[WeakReference[T]]|None]) -> INullable[T]:
        def tryGetValue() -> INullable[T]|None:
            node: IDoublyLinkedNode[WeakReference[T]]|None = getNode()

            if node is None:
                return GetNullValue()
            
            item: T|None = node.GetValue().TryGetValue()

            if item is None:
                node.Remove()
                
                return None

            return GetNullable(item)

        item: INullable[T]|None = tryGetValue()

        if item is None:
            while self.__items.HasItems() and (item := tryGetValue()) is None:
                pass
        
        return GetNullValue() if item is None else item
    
    def IsEmpty(self) -> bool:
        return self.__items.IsEmpty()
    
    def TryGetFirst(self) -> INullable[T]:
        return self.__TryGetValue(lambda: self.__items.GetFirst())
    def TryGetLast(self) -> INullable[T]:
        return self.__TryGetValue(lambda: self.__items.GetLast())
@final
class _ReadOnlyListUpdater[T: IDisposableBase](ValueFunctionUpdater[IReadOnlyList[T]]):
    def __init__(self, items: IList[WeakReference[T]], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IList[WeakReference[T]] = items
    
    def _GetValue(self) -> IReadOnlyList[T]:
        return _ReadOnlyList[T](self.__items)

class IObjectMonitor(IInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        pass
class IObjectFactory[T](IObjectMonitor):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def RegisterObject(self, item: T) -> None:
        pass

class ObjectFactoryBase[TIn, TOut: IDisposableBase](Abstract, IObjectFactory[TIn]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TOut]]) -> None:
            self.__readOnly = func
        
        super().__init__()

        self.__items: IList[WeakReference[TOut]] = List[WeakReference[TOut]]()

        self.__push: ConverterDelegate[TOut, INode] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__readOnly: IFunction[IReadOnlyList[TOut]] = _ReadOnlyListUpdater[TOut](self.__items, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__readOnly.GetValue()
    
    @final
    def __Push(self, obj: TOut) -> INode:
        cookie: IWeakReferenceRegister[TOut] = CreateWeakReferenceRegister(obj)
        node: IDoublyLinkedNode[WeakReference[TOut]] = self.__items.AddLast(cookie.GetCookie())

        cookie.RegisterNode(self._GetRemovable(obj, node))

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INode:
        self.__clear = self.__Clear

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INode:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: IDoublyLinkedNode[WeakReference[TOut]]) -> IRemovable:
        return node
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        pass
    
    @final
    def __Clear(self) -> None:
        for cookie in self.__items.AsQueuedGenerator():
            cookie.Invalidate()
        
        self.__push = self.__PushFirst
        self.__clear = NoAction
    
    @final
    def RegisterObject(self, item: TIn) -> None:
        self._Push(item)
    
    def InvalidateObjects(self) -> None:
        self.__clear()
class ObjectFactory[T](ObjectFactoryBase[T, IDisposableBase]):
    def __init__(self) -> None:
        super().__init__()

class DisposableObjectFactory[T: IDisposableBase](ObjectFactoryBase[T, T]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _Convert(self, item: T) -> T:
        return item

def ExtractKey(item: _SortedNodeBase|object) -> object:
    return item.GetKey() if isinstance(item, _SortedNodeBase) else item

class _SortedNodeBase(Abstract):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetKey(self) -> object:
        pass
@final
class _SortedNode[TKey: IExtendedHashableComparableValue, TValue: IDisposableBase](_SortedNodeBase, IExtendedComparable['_SortedNode[TKey, TValue]|TKey'], IRemovable):
    def __init__(self, key: TKey, obj: TValue, items: ISortedList[_SortedNode[TKey, TValue]]) -> None:
        super().__init__()

        self.__ref: ReferenceType[TValue] = ref(obj)
        self.__key: TKey = key
        self.__items: ISortedList[_SortedNode[TKey, TValue]] = items
    
    def TryGetValue(self) -> TValue|None:
        return self.__ref()
    
    def GetKey(self) -> TKey:
        return self.__key
    
    def CompareTo(self, item: _SortedNode[TKey, TValue]|TKey|object) -> bool|None:
        return self.GetKey().CompareTo(ExtractKey(item))
    
    def Equals(self, item: _SortedNode[TKey, TValue]|TKey|object) -> bool:
        return self.GetKey().Equals(ExtractKey(item))
    
    def Hash(self) -> int:
        return self.GetKey().Hash()
    
    def Remove(self) -> None:
        self.__items.RemoveAt(self.__items.BisectLeft(self.GetKey(), lambda n: n.GetKey()))

class SortedObjectFactoryBase[TKey: IExtendedHashableComparableValue, TIn, TOut: IDisposableBase](ObjectFactoryBase[TIn, TOut]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: ISortedList[_SortedNode[TKey, TOut]] = SortedList[_SortedNode[TKey, TOut]]()
    
    @final
    def __TryGetNode(self, key: TKey) -> _SortedNode[TKey, TOut]|None:
        items: ISortedList[_SortedNode[TKey, TOut]] = self._GetSortedItems()

        return items.TryGetValue(items.BisectLeft(key, lambda n: n.GetKey())).TryGetValue()
    
    @final
    def _GetSortedItems(self) -> ISortedList[_SortedNode[TKey, TOut]]:
        return self.__items
    
    @abstractmethod
    def _GetKey(self, item: TOut) -> TKey:
        pass
    
    def _GetRemovable(self, obj: TOut, node: IDoublyLinkedNode[WeakReference[TOut]]) -> IRemovable:
        items: ISortedList[_SortedNode[TKey, TOut]] = self._GetSortedItems()
        sortedNode: _SortedNode[TKey, TOut] = _SortedNode[TKey, TOut](self._GetKey(obj), obj, items)

        items.Add(sortedNode)

        return CompositeRemovable[TOut](node, sortedNode)
    
    @final
    def IsEmpty(self) -> bool:
        return self._GetSortedItems().IsEmpty()
    
    @final
    def ContainsKey(self, key: TKey) -> bool:
        node: _SortedNode[TKey, TOut]|None = self.__TryGetNode(key)

        return node is not None and node.GetKey().Equals(key)
    
    @final
    def TryGetByKey(self, key: TKey) -> INullable[TOut]:
        node: _SortedNode[TKey, TOut]|None = self.__TryGetNode(key)
        
        return GetNullableValue(None if node is None else (node.TryGetValue() if node.GetKey().Equals(key) else None))
    
    @final
    def BisectLeft(self, key: TKey) -> int:
        return self._GetSortedItems().BisectLeft(key, lambda n: n.GetKey())
    
    def InvalidateObjects(self) -> None:
        super().InvalidateObjects()
        
        self._GetSortedItems().Clear()
class SortedObjectFactory[TKey: IExtendedHashableComparableValue, TValue](SortedObjectFactoryBase[TKey, TValue, IDisposableBase]):
    def __init__(self) -> None:
        super().__init__()

class SortedDisposableObjectFactory[TKey: IExtendedHashableComparableValue, TValue: IDisposableBase](SortedObjectFactoryBase[TKey, TValue, TValue]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _Convert(self, item: TValue) -> TValue:
        return item