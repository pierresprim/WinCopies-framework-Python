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
        """Registers an object, which is then invalidated with the others registered here.

        The registrar may hold the object weakly, so the caller must keep it alive for as long as it must be invalidated. No handle is returned, so the object cannot be removed explicitly.

        Args:
            item: The object to register.
        """
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
        """Registers a monitor that another object owns, and holds it weakly.

        The monitor leaves the registrar once its owner drops it, so the owner must keep it alive for as long as it must be invalidated.

        Args:
            item: The monitor to register.

        Returns:
            A handle whose removal stops the invalidation of the monitor.
        """
        ...
class ICollectionRegistry[T: IObjectMonitor](ICollectionRegistrar[T], IObjectRegistry[T]):
    def __init__(self) -> None: super().__init__()