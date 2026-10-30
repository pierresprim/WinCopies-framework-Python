from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections import Generator
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Iteration import Generate, Iterate
from WinCopies.Collections.Registry import IObjectMonitor, IObjectRegistrar, IObjectRegistry, ICollectionRegistry
from WinCopies.Collections.Registry.Kernel import IRegistryAbstract, IWeakReferenceRegistryBase, IItemRegistryBase, RegistryAbstract, WeakReferenceRegistry as _WeakReferenceRegistry, ItemRegistry as _ItemRegistry
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Loop import DoForEachItem
from WinCopies.Delegates import NoAction, GetActionAsMethod
from WinCopies.Typing.Delegate import Action, Method, Converter
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Object import IWeakReferenceRegister, CreateWeakReferenceRegister

def _DoForEachItem[T](items: Generator[T], method: Method[T], action: Action|None) -> None:
    DoForEachItem(items, method, True if action is None else GetActionAsMethod(action))

class IRegistryBase[TIn, TOut](IRegistryAbstract[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self, action: Action|None = None) -> None:
        ...
class RegistryBase[TIn, TItem, TOut](RegistryAbstract[TIn, TItem, TOut], IRegistryBase[TIn, TOut]):
    def __init__(self) -> None: super().__init__()

class IWeakReferenceRegistry[T: IInvalidatable](IWeakReferenceRegistryBase[T], IRegistryBase[IWeakReferenceRegister[T], T]):
    def __init__(self) -> None: super().__init__()
class IItemRegistry[T: IObjectMonitor](IItemRegistryBase[T], IRegistryBase[T, T]):
    def __init__(self) -> None: super().__init__()

class WeakReferenceRegistry[T: IInvalidatable](_WeakReferenceRegistry[T], IWeakReferenceRegistry[T]):
    def __init__(self) -> None: super().__init__()
    
    @final
    def InvalidateObjects(self, action: Action|None = None) -> None:
        if self._GetItems().HasItems(): _DoForEachItem(Generate(self.TryRemoveFirst), lambda cookie: cookie.Invalidate(), action)
class ItemRegistry[T: IObjectMonitor](_ItemRegistry[T], IItemRegistry[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def InvalidateObjects(self, action: Action|None = None) -> None:
        if self._GetItems().HasItems(): _DoForEachItem(Iterate(self.TryGetFirstNode, lambda node: node.GetNext()), lambda node: node.GetValue().InvalidateObjects(), action)

def CreateWeakReferenceRegistry[T: IInvalidatable]() -> IWeakReferenceRegistry[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return WeakReferenceRegistry[T]()
def CreateItemRegistry[T: IObjectMonitor]() -> IItemRegistry[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return ItemRegistry[T]()

@final
class _Monitor(Abstract, IObjectMonitor):
    def __init__(self, monitor: IObjectMonitor) -> None:
        super().__init__()

        self.__monitor: IObjectMonitor = monitor

    def InvalidateObjects(self) -> None: self.__monitor.InvalidateObjects()
@final
class _Registrar[T](Abstract, IObjectRegistrar[T]):
    def __init__(self, registrar: IObjectRegistrar[T]) -> None:
        super().__init__()

        self.__registrar: IObjectRegistrar[T] = registrar

    def RegisterObject(self, item: T) -> None: self.__registrar.RegisterObject(item)

class ObjectRegistryBase[TIn, TOut: IInvalidatable](Abstract, IObjectRegistry[TIn]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IWeakReferenceRegistry[TOut] = CreateWeakReferenceRegistry()

        self.__push: Converter[TOut, INodeBase] = self.__PushFirst
        self.__clear: Action = NoAction

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[TIn] = _Registrar(self)
    
    @final
    def _GetItems(self) -> IReadOnlyList[TOut]:
        return self.__items.AsReadOnly()
    
    @final
    def __Push(self, obj: TOut) -> INodeBase:
        cookie: IWeakReferenceRegister[TOut] = CreateWeakReferenceRegister(obj)
        node: INodeBase = self.__items.Push(cookie)

        cookie.RegisterNode(self._GetRemovable(obj, node))

        return node
    @final
    def __PushFirst(self, obj: TOut) -> INodeBase:
        def finalize() -> None:
            self.__push = self.__PushFirst
            self.__clear = NoAction
        
        self.__push = self.__Push
        self.__clear = lambda: self.__items.InvalidateObjects(finalize)

        return self.__Push(obj)
    def _Push(self, item: TIn) -> INodeBase:
        return self.__push(self._Convert(item))
    
    def _GetRemovable(self, obj: TOut, node: INodeBase) -> IRemovable:
        return node
    
    @abstractmethod
    def _Convert(self, item: TIn) -> TOut:
        ...
    
    @final
    def RegisterObject(self, item: TIn) -> None: self._Push(item)
    
    def InvalidateObjects(self) -> None: self.__clear()

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[TIn]: return self.__registrar
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

class CollectionRegistry[T: IObjectMonitor](Abstract, ICollectionRegistry[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IItemRegistry[T] = CreateItemRegistry()

        self.__registerItem: Converter[T, IRemovable] = self.__Register
        self.__invalidateObjects: Action = NoAction

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[T] = _Registrar(self)

    @final
    def __Register(self, item: T) -> IRemovable:
        def register(item: T) -> IRemovable: return self.__items.Push(item)
        def finalize() -> None:
            self.__registerItem = self.__Register
            self.__invalidateObjects = NoAction
        
        self.__registerItem = register
        self.__invalidateObjects = lambda: self.__items.InvalidateObjects(finalize)

        return register(item)

    @final
    def _GetItems(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

    @final
    def RegisterObject(self, item: T) -> None: self.__registerItem(item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable: return _CollectionFactoryCookie(self.__registerItem(item))
    
    def InvalidateObjects(self) -> None: self.__invalidateObjects()

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[T]: return self.__registrar