from abc import abstractmethod

from WinCopies import IInterface

class IObjectMonitor(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def InvalidateObjects(self) -> None:
        ...
class IObjectFactory[T](IObjectMonitor):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def RegisterObject(self, item: T) -> None:
        ...