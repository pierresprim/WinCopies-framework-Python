from abc import abstractmethod
from enum import Enum
from typing import final

class IQueryBase[T]:
    def __init__(self):
        pass

    @abstractmethod
    def GetQuery(self) -> T|None:
        pass
    
    @abstractmethod
    def FormatTableName(self, tableName: str) -> str:
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