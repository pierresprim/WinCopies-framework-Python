from abc import abstractmethod
from typing import final

from WinCopies import IInterface
from WinCopies.Collections.Core import ITuple
from WinCopies.Collections.Enumeration.Core import IInvalidatableEnumerator
from WinCopies.Collections.Enumeration.Resumable import IInvalidatableResumableEnumerator
from WinCopies.Collections.Registry import IObjectMonitor, ICollectionRegistrar
from WinCopies.Collections.Registry.Collection import IEnumeratorRegistry as _IEnumeratorRegistry, ICollectionRegistries as _ICollectionRegistries, MonitorsBase as _MonitorsBase, CollectionRegistriesBase as _CollectionRegistries

class IEnumeratorMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateEnumerator[T](self, items: ITuple[T], strict: bool = False) -> IInvalidatableEnumerator[T]:
        ...
class IResumableEnumeratorMonitor(IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def CreateResumableEnumerator[T](self, items: ITuple[T], strict: bool = False) -> IInvalidatableResumableEnumerator[T]:
        ...

class IEnumeratorRegistry(_IEnumeratorRegistry[IEnumeratorMonitor], IEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
class IResumableEnumeratorRegistry(IEnumeratorRegistry, IResumableEnumeratorMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def AsMonitor(self) -> IResumableEnumeratorMonitor:
        ...

class ICollectionMonitors(ICollectionRegistrar[IObjectMonitor]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor:
        ...

class ICollectionRegistries(_ICollectionRegistries):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitors(self) -> ICollectionMonitors:
        ...

    @abstractmethod
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry:
        ...

class MonitorsBase[T: ICollectionRegistries](_MonitorsBase[T], ICollectionMonitors):
    def __init__(self, registries: T) -> None: super().__init__(registries)

    @final
    def GetEnumeratorMonitor(self) -> IResumableEnumeratorMonitor: return self._GetRegistries().GetEnumeratorRegistry().AsMonitor()
class Monitors(MonitorsBase[ICollectionRegistries]):
    def __init__(self, registries: ICollectionRegistries) -> None: super().__init__(registries)

class CollectionRegistriesBase[T: ICollectionMonitors](_CollectionRegistries[T, IResumableEnumeratorRegistry], ICollectionRegistries):
    def __init__(self) -> None: super().__init__()

    @final
    def AsMonitors(self) -> T: return self._AsMonitors()

    @final
    def GetEnumeratorRegistry(self) -> IResumableEnumeratorRegistry: return self._GetRegistry()
class CollectionRegistries(CollectionRegistriesBase[ICollectionMonitors]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CreateMonitors(self) -> ICollectionMonitors: return Monitors(self)