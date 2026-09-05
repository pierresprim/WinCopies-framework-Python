from __future__ import annotations

from abc import abstractmethod

from WinCopies import IInterface

class IResumable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Resume(self) -> None:
        ...

class IMovable(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def TryMoveToTop(self) -> bool|None:
        ...
    @abstractmethod
    def TryMoveToBottom(self) -> bool|None:
        ...

class IRemovable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Remove(self) -> None:
        ...

class INode(IMovable, IRemovable):
    def __init__(self) -> None: super().__init__()