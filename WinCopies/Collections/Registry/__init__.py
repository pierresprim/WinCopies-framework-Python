from abc import abstractmethod
from typing import final

from WinCopies import IInterface
from WinCopies.Collections.Generation import IRemovable

class IObjectMonitor(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        ...

class IActivationObject(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Activate(self) -> None:
        """Puts the entry of the monitor that received this object among the active entries of the collection registry that gave it, if it is not there yet.

        A monitor calls it once it has something to invalidate again. Calling it while the entry is active, or while the monitor is being invalidated, does nothing.
        """
        ...
class _IActivatableMonitor(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def _SetActivationObject(self, activationObject: IActivationObject) -> None:
        """
        Receives the object by which this monitor asks the collection registry that holds it to make it active again.

        The collection registry calls it at the registration of this monitor, once its entry is in its lists. A monitor is registered in one collection registry at most.

        Args:
            activationObject: The activation object.

        Raises:
            InvalidOperationError: This monitor already received an activation object."""
        ...
class IActivatableMonitor(IObjectMonitor, _IActivatableMonitor):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def IsActive(self) -> bool:
        """Tells whether this monitor has something to invalidate.

        A collection registry reads it at the registration of this monitor, to put it among its active or inactive entries, and after each invalidation of this monitor, to leave it active or not. The writes of the collection invalidate no inactive monitor, until it calls the activation object it received. This method may be called as soon as this monitor is registered, so this monitor must be fully constructed by then.

        Returns:
            True if this monitor has something to invalidate, False otherwise.
        """
        ...
class IActivatableRegistryBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def SetActivationObject(self, activationObject: IActivationObject) -> None:
        """
        Gives this registry the activation object that its owner received, so that its first registration after an invalidation makes its owner active again.

        The owner of this registry calls it when it receives its own activation object from the collection registry that holds it. A registry receives one activation object at most.

        Args:
            activationObject: The activation object that the owner of this registry received.

        Raises:
            InvalidOperationError: This registry already received an activation object.
        """
        ...
class IActivatableRegistry(IActivatableRegistryBase, _IActivatableMonitor):
    def __init__(self) -> None: super().__init__()

    @final
    def SetActivationObject(self, activationObject: IActivationObject) -> None: self._SetActivationObject(activationObject)

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

class ICollectionRegistrar[T: IActivatableMonitor](IObjectRegistrar[T]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def RegisterMonitor(self, item: T) -> IRemovable:
        """Registers a monitor that another object owns, and holds it weakly.

        The monitor leaves the registrar once its owner drops it, so the owner must keep it alive for as long as it must be invalidated. The registrar reads whether the monitor is active, and gives it its activation object.

        Args:
            item: The monitor to register.

        Returns:
            A handle whose removal stops the invalidation of the monitor.
        """
        ...
class ICollectionRegistry[T: IActivatableMonitor](ICollectionRegistrar[T], IObjectRegistry[T], IActivatableMonitor):
    def __init__(self) -> None: super().__init__()