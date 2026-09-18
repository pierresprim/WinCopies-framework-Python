from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import Abstract
from WinCopies.Collections.Generation import IRemovable, INode as INodeBase
from WinCopies.Collections.Generation.Registry import IObjectMonitor, IObjectRegistrar, IObjectRegistry
from WinCopies.Collections.Generation.Registry.Kernel import IWeakReferenceRegistry, IItemRegistry, CreateWeakReferenceRegistry, CreateItemRegistry
from WinCopies.Collections.Iteration import Iterate, Generate
from WinCopies.Collections.Linked.Doubly import IReadOnlyList
from WinCopies.Collections.Loop import DoForEachItem
from WinCopies.Delegates import NoAction
from WinCopies.Typing.Delegate import Action, Converter as ConverterDelegate
from WinCopies.Typing.Discard import IInvalidatable
from WinCopies.Typing.Object import IWeakReferenceRegister, CreateWeakReferenceRegister

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

        self.__push: ConverterDelegate[TOut, INodeBase] = self.__PushFirst
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
        def finalize(_: bool) -> None:
            self.__push = self.__PushFirst
            self.__clear = NoAction

        DoForEachItem(Generate(self.__items.TryRemoveFirst), lambda cookie: cookie.Invalidate(), finalize)
    
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

class ICollectionRegistry[T: IObjectMonitor](IObjectRegistry[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        ...

    def RegisterObject(self, item: T) -> None: self.RegisterMonitor(item)
class CollectionRegistry[T: IObjectMonitor](Abstract, ICollectionRegistry[T]):
    def __init__(self) -> None:
        super().__init__()

        self.__items: IItemRegistry[T] = CreateItemRegistry()

        self.__monitor: IObjectMonitor = _Monitor(self)
        self.__registrar: IObjectRegistrar[T] = _Registrar(self)

    @final
    def __Register(self, item: T) -> IRemovable:
        return self.__items.Push(item)

    @final
    def _GetItems(self) -> IReadOnlyList[T]:
        return self.__items.AsReadOnly()

    @final
    def RegisterObject(self, item: T) -> None: self.__Register(item)
    @final
    def RegisterMonitor(self, item: T) -> IRemovable: return _CollectionFactoryCookie(self.__Register(item))

    def InvalidateObjects(self) -> None:
        DoForEachItem(Iterate(self.__items.TryGetFirstNode, lambda node: node.GetNext()), lambda node: node.GetValue().InvalidateObjects(), True)

    @final
    def AsMonitor(self) -> IObjectMonitor: return self.__monitor
    @final
    def AsRegistrar(self) -> IObjectRegistrar[T]: return self.__registrar