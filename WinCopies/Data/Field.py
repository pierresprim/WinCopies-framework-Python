from abc import abstractmethod
from enum import auto, Enum, Flag
from typing import final

from WinCopies import IStringable
from WinCopies.Enum import EnsureFieldOf

class FieldType(Enum):
    Null = 0
    Boolean = 1
    Integer = 2
    Real = 3
    Text = 4

class IntegerMode(Enum):
    Byte = 1
    Short = 2
    Medium = 3
    Long = 4

class RealMode(Enum):
    Normal = 1
    Double = 2

class TextMode(Enum):
    Fixed = 1
    Variable = 2
    Text = 3

class FieldAttributes(Flag):
    Null = 0
    PrimaryKey = auto()
    AutoIncrement = auto()
    Unique = auto()
    Nullable = auto()

class IField(IStringable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetName(self) -> str:
        pass
    
    @abstractmethod
    def GetType(self) -> FieldType:
        pass

    @abstractmethod
    def GetAttribute(self) -> FieldAttributes:
        pass

class IModularField[T: Enum](IField):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetMode(self) -> T:
        pass

class Field(IField):
    def __init__(self, name: str, attribute: FieldAttributes):
        super().__init__()

        EnsureFieldOf(FieldAttributes, attribute)

        self.__name: str = name
        self.__attribute: FieldAttributes = attribute
    
    @final
    def GetName(self) -> str:
        return self.__name
    
    @final
    def GetAttribute(self) -> FieldAttributes:
        return self.__attribute

class ModularField[T: Enum](Field):
    def __init__(self, name: str, attribute: FieldAttributes, mode: T):
        super().__init__(name, attribute)

        self.__mode: T = mode
    
    @final
    def GetMode(self) -> T:
        return self.__mode

class GenericField(Field):
    def __init__(self, name: str, attribute: FieldAttributes):
        super().__init__(name, attribute)
    
    @final
    def GetType(self) -> FieldType:
        return FieldType.Null

class BooleanField(Field):
    def __init__(self, name: str, attribute: FieldAttributes):
        super().__init__(name, attribute)
    
    @final
    def GetType(self) -> FieldType:
        return FieldType.Boolean

class IntegerField(ModularField[IntegerMode]):
    def __init__(self, name: str, attribute: FieldAttributes, mode: IntegerMode):
        super().__init__(name, attribute, mode)
    
    @final
    def GetType(self) -> FieldType:
        return FieldType.Integer

class RealField(ModularField[RealMode]):
    def __init__(self, name: str, attribute: FieldAttributes, mode: RealMode):
        super().__init__(name, attribute, mode)
    
    @final
    def GetType(self) -> FieldType:
        return FieldType.Real

class TextField(ModularField[TextMode]):
    def __init__(self, name: str, attribute: FieldAttributes, mode: TextMode):
        super().__init__(name, attribute, mode)

    @final
    def GetType(self) -> FieldType:
        return FieldType.Text