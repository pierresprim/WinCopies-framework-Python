from __future__ import annotations

from abc import abstractmethod
from typing import final, Self

from WinCopies import IDisposableBase, Abstract
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Factory import IObjectFactory
from WinCopies.Collections.Linked.Doubly import IReadOnlyList, IReadWriteList
from WinCopies.Collections.Linked.Doubly.Core import ListBase, ListNodeBase
from WinCopies.Collections.Linked.Doubly.Node import IListCookie, INodeCookie, IDoublyLinkedNodeBase, IDoublyLinkedNode, DoublyLinkedNode
from WinCopies.Collections.Linked.Node import IReadWriteLinkedNode
from WinCopies.Delegates import NoAction
from WinCopies.Typing import INullable, GetNullable, GetNullValue
from WinCopies.Typing.Delegate import Action, Method, Function, Converter as ConverterDelegate, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Generic import IGenericConstraintImplementation
from WinCopies.Typing.Object import IWeakReferenceRegister, WeakReference, CreateWeakReferenceRegister

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

@final
class _ReadOnlyListBase[T: IDisposableBase](Abstract, IReadOnlyList[WeakReference[T]]):
    def __init__(self, items: IReadWriteList[WeakReference[T]]) -> None:
        super().__init__()

        self.__items: IReadWriteList[WeakReference[T]] = items
    
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()
    
    def TryGetFirst(self) -> INullable[WeakReference[T]]: return self.__items.TryGetFirst()
    def TryGetLast(self) -> INullable[WeakReference[T]]: return self.__items.TryGetLast()
@final
class _ReadOnlyList[T: IDisposableBase](Abstract, IReadOnlyList[T]):
    def __init__(self, items: IReadWriteList[WeakReference[T]]) -> None:
        super().__init__()

        self.__items: IReadWriteList[WeakReference[T]] = items
    
    def IsEmpty(self) -> bool: return self.__items.IsEmpty()
    
    def __TryGetValue(self, getNode: Function[IReadWriteLinkedNode[WeakReference[T]]|None]) -> INullable[T]:
        def tryGetValue() -> INullable[T]|None:
            node: IReadWriteLinkedNode[WeakReference[T]]|None = getNode()

            if node is None: return GetNullValue()
            
            item: T|None = node.GetValue().TryGetValue()

            if item is None:
                node.Remove()
                
                return None

            return GetNullable(item)

        item: INullable[T]|None = tryGetValue()

        if item is None:
            while self.__items.HasItems() and (item := tryGetValue()) is None: pass
        
        return GetNullValue() if item is None else item
    
    def TryGetFirst(self) -> INullable[T]: return self.__TryGetValue(lambda: self.__items.GetFirstNode())
    def TryGetLast(self) -> INullable[T]: return self.__TryGetValue(lambda: self.__items.GetLastNode())

@final
class _ReadOnlyListBaseUpdater[T: IDisposableBase](ValueFunctionUpdater[IReadOnlyList[WeakReference[T]]]):
    def __init__(self, items: IReadWriteList[WeakReference[T]], updater: Method[IFunction[IReadOnlyList[WeakReference[T]]]]) -> None:
        super().__init__(updater)

        self.__items: IReadWriteList[WeakReference[T]] = items
    
    def _GetValue(self) -> IReadOnlyList[WeakReference[T]]: return _ReadOnlyListBase[T](self.__items)
@final
class _ReadOnlyListUpdater[T: IDisposableBase](ValueFunctionUpdater[IReadOnlyList[T]]):
    def __init__(self, items: IReadWriteList[WeakReference[T]], updater: Method[IFunction[IReadOnlyList[T]]]) -> None:
        super().__init__(updater)

        self.__items: IReadWriteList[WeakReference[T]] = items
    
    def _GetValue(self) -> IReadOnlyList[T]: return _ReadOnlyList[T](self.__items)

@final
class _List[T: IDisposableBase](ListBase[WeakReference[T], "_Node[T]", IDoublyLinkedNode[WeakReference[T]]], IGenericConstraintImplementation[IDoublyLinkedNode[WeakReference[T]]]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[WeakReference[T]]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__readOnly: IFunction[IReadOnlyList[WeakReference[T]]] = _ReadOnlyListBaseUpdater[T](self, update) # type: ignore[no-redef]
    
    def _CreateNode(self, value: WeakReference[T]) -> _Node[T]:
        return _Node[T](value, self, self, self._GetCookie(), None, None)
    
    def _GetNodeAsClass(self, node: _Node[T]) -> IDoublyLinkedNode[WeakReference[T]]:
        return node
    def _GetNodeAsInterface(self, node: _Node[T]) -> IDoublyLinkedNodeBase[WeakReference[T], _Node[T]]:
        return node
    
    def _GetPreviousNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetPreviousNode()
    def _GetNextNode(self, node: _Node[T]) -> _Node[T]|None:
        return node.GetNextNode()
    
    def _UnregisterNode(self, node: _Node[T]) -> None:
        return node._Unregister() # pyright: ignore[reportPrivateUsage]
    
    def AsReadOnly(self) -> IReadOnlyList[WeakReference[T]]:
        return self.__readOnly.GetValue()

@final
class _Node[T: IDisposableBase](DoublyLinkedNode[WeakReference[T], "_Node[T]", IReadWriteList[WeakReference[T]], _List[T]], ListNodeBase["_Node[T]"], IDoublyLinkedNode[WeakReference[T]], IGenericConstraintImplementation[IReadWriteList[WeakReference[T]]]):
    def __init__(self, value: WeakReference[T], l: _List[T]|None, itemCookie: IListCookie[_Node[T]], cookie: INodeCookie[_Node[T]], previousNode: Self|None, nextNode: Self|None) -> None: super().__init__(value, l, itemCookie, cookie, previousNode, nextNode)
    
    def _AsLinkedNode(self, node: _Node[T]) -> _Node[T]:
        return node
    
    def _GetListAsClass(self, l: _List[T]) -> IReadWriteList[WeakReference[T]]:
        return l
    
    def _AsNode(self) -> _Node[T]:
        return self
    
    def _CreateNode(self, value: WeakReference[T], previous: Self|None, next: Self|None) -> _Node[T]:
        return _Node[T](value, self._GetInnerList(), self._GetItemCookie(), self._GetCookie(), previous, next)
    
    def GetList(self) -> IReadWriteList[WeakReference[T]]|None: return self._GetList()

class ObjectFactoryBase[TIn, TOut: IDisposableBase](Abstract, IObjectFactory[TIn]):
    def __init__(self) -> None:
        def update(func: IFunction[IReadOnlyList[TOut]]) -> None: self.__readOnly = func
        
        super().__init__()

        self.__items: IReadWriteList[WeakReference[TOut]] = _List[TOut]()

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
        cookie: WeakReference[TOut]|None = None

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