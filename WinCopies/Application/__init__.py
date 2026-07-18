from abc import abstractmethod
from typing import final

from WinCopies import IInterface, Abstract

class IDescription(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetName(self) -> str: ...
    @abstractmethod
    def GetDescription(self) -> str: ...
class Description(Abstract, IDescription):
    def __init__(self, name: str, description: str) -> None:
        super().__init__()

        self.__name: str = name
        self.__description: str = description
    
    @final
    def GetName(self) -> str: return self.__name
    @final
    def GetDescription(self) -> str: return self.__description