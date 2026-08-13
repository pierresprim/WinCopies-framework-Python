from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies import IDisposableBase, Abstract
from WinCopies.Collections.Core import IClearable
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Factory import IObjectMonitor, IObjectFactory
from WinCopies.Collections.Linked.Doubly import IReadOnlyList, IReadWriteList
from WinCopies.Collections.Linked.Doubly.Core import ListBase, ListNodeBase
from WinCopies.Collections.Linked.Doubly.Node import IListCookie, INodeCookie, IDoublyLinkedNode, DoublyLinkedNode
from WinCopies.Collections.Linked.Node import ILinkedNode, IReadWriteLinkedNode
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Action, Method, Function, Converter as ConverterDelegate, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraintImplementation
from WinCopies.Typing.Object import IWeakReferenceRegister, IWeakReference, CreateWeakReferenceRegister

class CompositeRemovable(Abstract, IRemovable):
    def __init__(self, node: IRemovable, obj: IRemovable) -> None:
        def remove() -> None:
            self.__node.Remove()
            self.__obj.Remove()

            self.__remove = NoAction

        super().__init__()

        self.__node: IRemovable = node
        self.__obj: IRemovable = obj
        
        self.__remove: Action = remove # type: ignore[no-redef]
    
    def Remove(self) -> None: self.__remove()

class _ReadOnlyListAbstract[TIn, TOut](Abstract, IReadOnlyList[TOut]):
    def __init__(self, items: IReadWriteList[TIn]) -> None:
        super().__init__()

        self.__items: IReadWriteList[TIn] = items

    @final
    def _GetItems(self) -> IReadWriteList[TIn]:
        return self.__items
    
    @final
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()

@final
class _ReadOnlyCollection[T](_ReadOnlyListAbstract[T, T]):
    def __init__(self, items: IReadWriteList[T]) -> None: super().__init__(items)
    
    def TryGetFirst(self) -> INullable[T]: return self._GetItems().TryGetFirst()
    def TryGetLast(self) -> INullable[T]: return self._GetItems().TryGetLast()

@final
class _ReadOnlyList[T: IDisposableBase](_ReadOnlyListAbstract[IWeakReference[T], T]):
    def __init__(self, items: IReadWriteList[IWeakReference[T]]) -> None: super().__init__(items)
    
    def __TryGetValue(self, getNode: Function[IReadWriteLinkedNode[IWeakReference[T]]|None]) -> INullable[T]:
        def tryGetValue() -> INullable[T]|None:
            node: IReadWriteLinkedNode[IWeakReference[T]]|None = getNode()

            if node is None: return GetNullValue()
            
            item: T|None = node.GetValue().TryGetValue()

            if item is None:
                node.Remove()
                
                return None

            return GetNullable(item)

        item: INullable[T]|None = tryGetValue()

        if item is None:
            while self._GetItems().HasItems() and (item := tryGetValue()) is None: pass
        
        return GetNullValue() if item is None else item
    
    def TryGetFirst(self) -> INullable[T]: return self.__TryGetValue(lambda: self._GetItems().GetFirstNode())
    def TryGetLast(self) -> INullable[T]: return self.__TryGetValue(lambda: self._GetItems().GetLastNode())

class _ReadOnlyListUpdaterBase[TItem, TList](ValueFunctionUpdater[TList]):
    def __init__(self, items: IReadWriteList[TItem], updater: Method[IFunction[TList]]) -> None:
        super().__init__(updater)

        self.__items: IReadWriteList[TItem] = items

    @abstractmethod
    def _GetItems(self, items: IReadWriteList[TItem]) -> TList:
        ...

    @final
    def _GetValue(self) -> TList: return self._GetItems(self.__items)

@final
class _ReadOnlyListBaseUpdater[T: IDisposableBase](_ReadOnlyListUpdaterBase[IWeakReference[T], IReadOnlyList[IWeakReference[T]]]):
    def __init__(self, items: IReadWriteList[IWeakReference[T]], updater: Method[IFunction[IReadOnlyList[IWeakReference[T]]]]) -> None: super().__init__(items, updater)
    
    def _GetItems(self, items: IReadWriteList[IWeakReference[T]]) -> IReadOnlyList[IWeakReference[T]]: return _ReadOnlyCollection[IWeakReference[T]](items)
@final
class _ReadOnlyListUpdater[T: IDisposableBase](_ReadOnlyListUpdaterBase[IWeakReference[T], IReadOnlyList[T]]):
    def __init__(self, items: IReadWriteList[IWeakReference[T]], updater: Method[IFunction[IReadOnlyList[T]]]) -> None: super().__init__(items, updater)
    
    def _GetItems(self, items: IReadWriteList[IWeakReference[T]]) -> IReadOnlyList[T]: return _ReadOnlyList[T](items)

@final
class _ReadOnlyCollectionUpdater[T: IObjectMonitor](_ReadOnlyListUpdaterBase[T, IReadOnlyList[T]]):
    def __init__(self, items: IReadWriteList[T], updater: Method[IFunction[IReadOnlyList[T]]]) -> None: super().__init__(items, updater)
    
    def _GetItems(self, items: IReadWriteList[T]) -> IReadOnlyList[T]: return _ReadOnlyCollection[T](items)

class _ListBase[TItem, TNode, TList: IClearable](ListBase[TItem, TNode, IDoublyLinkedNode[TItem]], IGenericConstraintImplementation[IDoublyLinkedNode[TItem]]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TItem]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyList[TItem]] = self._CreateUpdater(update) # type: ignore[no-redef]

    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[IReadOnlyList[TItem]]]) -> IFunction[IReadOnlyList[TItem]]:
        ...

    @abstractmethod
    def _GetNodeAsObject(self, node: TNode) -> _NodeBase[TItem, TNode, TList]:
        ...

    @final
    def _UnregisterNode(self, node: TNode) -> None:
        return self._GetNodeAsObject(node)._Unregister() # pyright: ignore[reportPrivateUsage]

    @final
    def AsReadOnly(self) -> IReadOnlyList[TItem]:
        return self.__readOnly.GetValue()

@final
class _Collection[T: IObjectMonitor](_ListBase[T, "_CollectionNode[T]", "_Collection[T]"]):
    def __init__(self) -> None: super().__init__()

    def _CreateUpdater(self, updater: Method[IFunction[IReadOnlyList[T]]]) -> IFunction[IReadOnlyList[T]]: return _ReadOnlyCollectionUpdater[T](self, updater)
    
    def _CreateNode(self, value: T) -> _CollectionNode[T]: return _CollectionNode[T](value, self, self, self._GetCookie(), None, None)

    def _GetNodeAsObject(self, node: _CollectionNode[T]) -> _CollectionNode[T]: return node
    
    def _GetNodeAsClass(self, node: _CollectionNode[T]) -> IDoublyLinkedNode[T]: return node
    def _GetNodeAsInterface(self, node: _CollectionNode[T]) -> _CollectionNode[T]: return node
    
    def _GetPreviousNode(self, node: _CollectionNode[T]) -> _CollectionNode[T]|None: return node.GetPreviousNode()
    def _GetNextNode(self, node: _CollectionNode[T]) -> _CollectionNode[T]|None: return node.GetNextNode()
@final
class _List[T: IDisposableBase](_ListBase[IWeakReference[T], "_Node[T]", "_List[T]"]):
    def __init__(self) -> None: super().__init__()

    def _CreateUpdater(self, updater: Method[IFunction[IReadOnlyList[IWeakReference[T]]]]) -> IFunction[IReadOnlyList[IWeakReference[T]]]: return _ReadOnlyListBaseUpdater[T](self, updater)
    
    def _CreateNode(self, value: IWeakReference[T]) -> _Node[T]: return _Node[T](value, self, self, self._GetCookie(), None, None)

    def _GetNodeAsObject(self, node: _Node[T]) -> _Node[T]: return node
    
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[IWeakReference[T]]: return node
    def _GetNodeAsInterface(self, node: _Node[T]) -> _Node[T]: return node
    
    def _GetPreviousNode(self, node: _Node[T]) -> _Node[T]|None: return node.GetPreviousNode()
    def _GetNextNode(self, node: _Node[T]) -> _Node[T]|None: return node.GetNextNode()

class _NodeBase[TItem, TNode, TList: IClearable](DoublyLinkedNode[TItem, TNode, IReadWriteList[TItem], TList], ListNodeBase[TNode], IDoublyLinkedNode[TItem], IGenericConstraintImplementation[IReadWriteList[TItem]]):
    def __init__(self, value: TItem, l: TList|None, itemCookie: IListCookie[TNode], cookie: INodeCookie[TNode], previousNode: TNode|None, nextNode: TNode|None) -> None: super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)

    @final
    def GetList(self) -> IReadWriteList[TItem]|None: return self._GetList()

@final
class _Node[T: IDisposableBase](_NodeBase[IWeakReference[T], "_Node[T]", _List[T]]):
    def __init__(self, value: IWeakReference[T], l: _List[T]|None, itemCookie: IListCookie[_Node[T]], cookie: INodeCookie[_Node[T]], previousNode: Self|None, nextNode: Self|None) -> None: super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _Node[T]) -> _Node[T]:
        return node
    
    def _GetListAsClass(self, l: _List[T]) -> IReadWriteList[IWeakReference[T]]:
        return l
    
    def _AsNode(self) -> _Node[T]:
        return self
    
    def _CreateNode(self, value: IWeakReference[T], previous: Self|None, next: Self|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), self._GetItemCookie(), self._GetCookie(), previous, next)
@final
class _CollectionNode[T: IObjectMonitor](_NodeBase[T, "_CollectionNode[T]", _Collection[T]]):
    def __init__(self, value: T, l: _Collection[T]|None, itemCookie: IListCookie[_CollectionNode[T]], cookie: INodeCookie[_CollectionNode[T]], previousNode: Self|None, nextNode: Self|None) -> None: super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _CollectionNode[T]) -> _CollectionNode[T]:
        return node
    
    def _GetListAsClass(self, l: _Collection[T]) -> IReadWriteList[T]:
        return l
    
    def _AsNode(self) -> _CollectionNode[T]:
        return self
    
    def _CreateNode(self, value: T, previous: Self|None, next: Self|None) -> _CollectionNode[T]:
        return _CollectionNode[T](value, self._GetInnerList(), self._GetItemCookie(), self._GetCookie(), previous, next)

class ObjectFactoryBase[TIn, TOut: IDisposableBase](Abstract, IObjectFactory[TIn]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TOut]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__items: IReadWriteList[IWeakReference[TOut]] = _List[TOut]()

        self.__push: ConverterDelegate[TOut, INodeBase] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__readOnly: IFunction[IReadOnlyList[TOut]] = _ReadOnlyListUpdater[TOut](self.__items, update) # type: ignore[no-redef]
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__readOnly.GetValue()
    
    @final
    def __Push(self, obj: TOut) -> INodeBase:
        cookie: IWeakReferenceRegister[TOut] = CreateWeakReferenceRegister(obj)
        node: INodeBase = self.__items.AddLastNode(cookie.GetCookie())

        cookie.RegisterNode(self._GetRemovable(obj, node))

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INodeBase:
        self.__push = self.__Push
        self.__clear = self.__Clear

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INodeBase:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> IRemovable:
        return node
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
    
    @final
    def __Clear(self) -> None:
        cookie: IWeakReference[TOut]|None = None

        while (cookie := self.__items.TryRemoveFirst().TryGetValue()) is not None:
            cookie.Invalidate()
        
        self.__push = self.__PushFirst
        self.__clear = NoAction
    
    @final
    def RegisterObject(self, item: TIn) -> None: self._Push(item)
    
    def InvalidateObjects(self) -> None: self.__clear()
class ObjectFactory[T](ObjectFactoryBase[T, IDisposableBase]):
    def __init__(self) -> None: super().__init__()

class DisposableObjectFactory[T: IDisposableBase](ObjectFactoryBase[T, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: T) -> T: return item

@final
class _CollectionFactoryCookie(Abstract, IRemovable):
    def __init__(self, node: IRemovable) -> None:
        super().__init__()

        self.__node: IRemovable = node

    def Remove(self) -> None: self.__node.Remove()

class ICollectionFactory[T: IObjectMonitor](IObjectFactory[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        ...

    def RegisterObject(self, item: T) -> None: self.RegisterMonitor(item)
class CollectionFactory[T: IObjectMonitor](Abstract, ICollectionFactory[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IReadWriteList[T] = _Collection[T]()

    @final
    def __Register(self, item: T) -> IRemovable:
        return self.__items.AddLastNode(item)

    @final
    def _GetItems(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

    @final
    def RegisterObject(self, item: T) -> None: self.__Register(item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable: return _CollectionFactoryCookie(self.__Register(item))

    def InvalidateObjects(self) -> None:
        node: ILinkedNode[T]|None = self.__items.GetFirstNode()

        while node is not None:
            node.GetValue().InvalidateObjects()

            node = node.GetNext()