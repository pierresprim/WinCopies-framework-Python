from abc import abstractmethod
from typing import final

from WinCopies import Abstract

from WinCopies.Collections.Generation import IRemovable
from WinCopies.Collections.Registry import IObjectMonitor, ICollectionRegistrar, ICollectionRegistry
from WinCopies.Collections.Registry.Core import CollectionRegistry
from WinCopies.Collections.Extensions import IResumableEnumeratorMonitor
from WinCopies.Collections.Extensions.Enumeration import IResumableEnumeratorRegistry, ResumableEnumeratorRegistry

class ICollectionMonitors(ICollectionRegistrar[IObjectMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor:
        ...

class ICollectionRegistries(ICollectionRegistry[IObjectMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitors(self) -> ICollectionMonitors:
        ...

    @abstractmethod
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry:
        ...

class MonitorsBase[T: ICollectionRegistries](Abstract, ICollectionMonitors):
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

    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor: return self._GetRegistries().GetEnumeratorRegistry().AsMonitor()
class Monitors(MonitorsBase[ICollectionRegistries]):
    def __init__(self, registries: ICollectionRegistries) -> None: super().__init__(registries)

class CollectionRegistriesBase[T: ICollectionMonitors](CollectionRegistry[IObjectMonitor], ICollectionRegistries):
    def __init__(self) -> None:
        super().__init__()

        self.__monitors: T = self._CreateMonitor()
        self.__registry: IResumableEnumeratorRegistry = self._CreateRegistry(ResumableEnumeratorRegistry())

    @abstractmethod
    def _CreateMonitor(self) -> T:
        ...
    @final
    def _CreateRegistry[U: IObjectMonitor](self, registry: U) -> U:
        self.RegisterObject(registry)

        return registry

    @final
    def AsMonitors(self) -> T: return self.__monitors

    @final
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry: return self.__registry
class CollectionRegistries(CollectionRegistriesBase[ICollectionMonitors]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateMonitor(self) -> ICollectionMonitors: return Monitors(self)