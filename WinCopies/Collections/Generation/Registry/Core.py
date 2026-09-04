from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Registry import IObjectMonitor, IObjectRegistry
from WinCopies.Collections.Generation.Registry.Kernel import _ReadOnlyListUpdater, _List, _Collection
from WinCopies.Collections.Linked.Doubly import IReadOnlyList, IReadWriteList
from WinCopies.Collections.Linked.Node import ILinkedNode
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Converter as ConverterDelegate, IFunction
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Object import IWeakReferenceRegister, IWeakReference, CreateWeakReferenceRegister

class ObjectRegistryBase[TIn, TOut: IInvalidatable](Abstract, IObjectRegistry[TIn]):
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
class ObjectRegistry[T](ObjectRegistryBase[T, IInvalidatable]):
    def __init__(self) -> None: super().__init__()

class InvalidatableObjectRegistry[T: IInvalidatable](ObjectRegistryBase[T, T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def _Convert(self, item: T) -> T: return item

@final
class _CollectionFactoryCookie(Abstract, IRemovable):
    def __init__(self, node: IRemovable) -> None:
        super().__init__()

        self.__node: IRemovable = node

    def Remove(self) -> None: self.__node.Remove()

class ICollectionRegistry[T: IObjectMonitor](IObjectRegistry[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        ...

    def RegisterObject(self, item: T) -> None: self.RegisterMonitor(item)
class CollectionRegistry[T: IObjectMonitor](Abstract, ICollectionRegistry[T]):
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