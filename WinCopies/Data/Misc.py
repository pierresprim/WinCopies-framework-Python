from abc import abstractmethod
from enum import Enum
from typing import final

from WinCopies import IInterface

class ITableNameFormater(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def FormatTableName(self, name: str) -> str:
        pass

class IQueryBase[T](ITableNameFormater):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def GetQuery(self) -> T|None:
        pass

class JoinType(Enum):
    Null = 0
    Inner = 1
    Outer = 2

    @final
    def __str__(self) -> str:
        def getName() -> str:
            return self.name.upper()
        
        match self:
            case JoinType.Inner | JoinType.Outer:
                return getName()
            
            case _:
                return ''