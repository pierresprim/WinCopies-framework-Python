from abc import abstractmethod

from WinCopies import IInterface, Abstract
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Typing.Discard import IInvalidatable

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

class IInvalidationRegistrarBase(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Unregister(self) -> None:
        ...

class IInvalidationRegistrar(IInvalidationRegistrarBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Register(self, cookie: IInvalidatable) -> None:
        ...
class InvalidationRegistrar(Abstract, IInvalidationRegistrar):
    def __init__(self) -> None: super().__init__()

class IManagedInvalidationRegistrar(IInvalidationRegistrarBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Push(self, invalidationRegistrar: IInvalidationRegistrar) -> IRemovable:
        ...

    @abstractmethod
    def Register(self) -> None:
        ...