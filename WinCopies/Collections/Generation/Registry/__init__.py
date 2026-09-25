from abc import abstractmethod

from WinCopies import IInterface
from WinCopies.Collections.Generation import IRemovable

class IObjectMonitor(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        ...
class IObjectRegistrar[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def RegisterObject(self, item: T) -> None:
        ...
class IObjectRegistry[T](IObjectRegistrar[T], IObjectMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def AsMonitor(self) -> IObjectMonitor:
        ...
    @abstractmethod
    def AsRegistrar(self) -> IObjectRegistrar[T]:
        ...

class ICollectionRegistrar[T: IObjectMonitor](IObjectRegistrar[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        ...
class ICollectionRegistry[T: IObjectMonitor](ICollectionRegistrar[T], IObjectRegistry[T]):
    def __init__(self) -> None: super().__init__()