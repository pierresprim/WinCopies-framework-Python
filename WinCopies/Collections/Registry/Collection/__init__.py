from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract

from WinCopies.Collections.Enumeration.Core import IInvalidatableEnumeratorBase
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Registry import IObjectMonitor, ICollectionRegistrar, ICollectionRegistry
from WinCopies.Collections.Registry.Core import CollectionRegistry, InvalidatableObjectRegistry
from WinCopies.Collections.Registry.Invalidation import InvalidationRegistrar

from WinCopies.Typing.Delegate import Method, IFunction, ValueFunctionUpdater
from WinCopies.Typing.Discard import IInvalidatable

@final
class _Registry(InvalidatableObjectRegistry[IInvalidatable]):
    def __init__(self) -> None: super().__init__()

    def RegisterEnumerator(self, item: IInvalidatable) -> IRemovable:
        return self._Push(item)
@final
class _Registrar(InvalidationRegistrar):
    def __init__(self, registry: _Registry) -> None:
        super().__init__()

        self.__registry: _Registry = registry
        self.__node: IRemovable|None = None

    def Register(self, cookie: IInvalidatable) -> None:
        self.__node = self.__registry.RegisterEnumerator(cookie)
    def Unregister(self) -> None:
        node: IRemovable|None = self.__node

        if node is not None: node.Remove()

class IEnumeratorRegistryBase(IObjectMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterEnumerator(self, enumerator: IInvalidatableEnumeratorBase, strict: bool = False) -> None:
        ...
class IEnumeratorRegistry[T](IEnumeratorRegistryBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitor(self) -> T:
        ...

class ICollectionRegistries(ICollectionRegistry[IObjectMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitors(self) -> ICollectionRegistrar[IObjectMonitor]:
        ...

    @abstractmethod
    def GetEnumeratorRegistry(self) -> IEnumeratorRegistryBase:
        ...

class IViewProvider(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _InvalidateViews(self) -> None:
        ...

class IManagedEnumerableBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCollectionRegistries(self) -> ICollectionRegistries:
        ...
class IManagedEnumerable[T: ICollectionRegistries](IManagedEnumerableBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetCollectionRegistries(self) -> T:
        ...

class IManagedCollectionBase(IManagedEnumerableBase, IViewProvider):
    def __init__(self) -> None: super().__init__()

    @final
    def _InvalidateViews(self) -> None: self._GetCollectionRegistries().InvalidateObjects()
class IManagedCollection[T: ICollectionRegistries](IManagedCollectionBase, IManagedEnumerable[T]):
    def __init__(self) -> None: super().__init__()

class MonitorsBase[T: ICollectionRegistries](Abstract, ICollectionRegistrar[IObjectMonitor]):
    def __init__(self, registries: T) -> None:
        super().__init__()

        self.__registries: T = registries

    @final
    def _GetRegistries(self) -> T:
        return self.__registries

    @final
    def RegisterMonitor(self, item: IObjectMonitor) -> IRemovable: return self._GetRegistries().RegisterMonitor(item)
    @final
    def RegisterObject(self, item: IObjectMonitor) -> None: self.RegisterMonitor(item)
class Monitors(MonitorsBase[ICollectionRegistries]):
    def __init__(self, registries: ICollectionRegistries) -> None: super().__init__(registries)

class EnumeratorMonitorUpdater[TMonitor, TRegistry](ValueFunctionUpdater[TMonitor]):
    def __init__(self, registry: TRegistry, updater: Method[IFunction[TMonitor]]) -> None:
        super().__init__(updater)

        self.__registry: TRegistry = registry
    
    @final
    def _GetRegistry(self) -> TRegistry:
        return self.__registry

class DefaultEnumeratorRegistry(Abstract, IEnumeratorRegistryBase):
    def __init__(self) -> None:
        super().__init__()

        self.__registry: _Registry = _Registry()

    @final
    def _GetRegistry(self) -> _Registry:
        return self.__registry
    
    @final
    def RegisterEnumerator(self, enumerator: IInvalidatableEnumeratorBase, strict: bool = False) -> None: enumerator.Register(self._GetRegistry()) if strict else enumerator.AddRegistrar(_Registrar(self._GetRegistry()))

    @final
    def InvalidateObjects(self) -> None: self._GetRegistry().InvalidateObjects()

class EnumeratorRegistryBase[T](DefaultEnumeratorRegistry):
    def __init__(self) -> None:
        def update(func: IFunction[T]) -> None: self.__monitor = func
        
        super().__init__()

        self.__monitor: IFunction[T] = self._CreateUpdater(update) # type: ignore[no-redef]

    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[T]]) -> ValueFunctionUpdater[T]:
        ...
    
    @final
    def _AsMonitor(self) -> T:
        return self.__monitor.GetValue()
class EnumeratorRegistry[TMonitor, TRegistry](EnumeratorRegistryBase[TMonitor]):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _CreateUpdater(self, updater: Method[IFunction[TMonitor]]) -> EnumeratorMonitorUpdater[TMonitor, TRegistry]:
        ...

class CollectionRegistriesBase[TMonitors, TRegistry: IObjectMonitor](CollectionRegistry[IObjectMonitor], ICollectionRegistries):
    def __init__(self) -> None:
        super().__init__()

        self.__monitors: TMonitors = self._CreateMonitors()
        self.__registry: TRegistry = self._CreateRegistry(self._CreateEnumeratorRegistry())

    @final
    def _CreateRegistry[U: IObjectMonitor](self, registry: U) -> U:
        self.RegisterObject(registry)

        return registry

    @abstractmethod
    def _CreateMonitors(self) -> TMonitors:
        ...
    @abstractmethod
    def _CreateEnumeratorRegistry(self) -> TRegistry:
        ...

    @final
    def _AsMonitors(self) -> TMonitors:
        return self.__monitors
    @final
    def _GetRegistry(self) -> TRegistry:
        return self.__registry
class CollectionRegistries(CollectionRegistriesBase[ICollectionRegistrar[IObjectMonitor], IEnumeratorRegistryBase]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateEnumeratorRegistry(self) -> IEnumeratorRegistryBase: return DefaultEnumeratorRegistry()

    @final
    def _CreateMonitors(self) -> ICollectionRegistrar[IObjectMonitor]: return Monitors(self)

    @final
    def AsMonitors(self) -> ICollectionRegistrar[IObjectMonitor]: return self._AsMonitors()

    @final
    def GetEnumeratorRegistry(self) -> IEnumeratorRegistryBase: return self._GetRegistry()