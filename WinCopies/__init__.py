# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from enum import Enum
from types import TracebackType
from typing import final, Self

class IInterface:
    def __init__(self):
        pass

class Abstract(ABC, IInterface):
    def __init__(self):
        super().__init__()

class IBooleanable(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ToBool(self) -> bool:
        pass
class INullableBooleanable(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ToNullableBoolean(self) -> NullableBoolean:
        pass
    
    @abstractmethod
    def ToNullableBool(self) -> bool|None:
        return ToNullableBool(self.ToNullableBoolean())

class BooleanableEnum(Enum):
    def __bool__(self) -> bool:
        return self.value >= 0

class NullableBoolean(BooleanableEnum):
    BoolFalse = -1
    Null = 0
    BoolTrue = 1
    
    def Not(self) -> NullableBoolean:
        return NullableBoolean.BoolFalse if self else NullableBoolean.BoolTrue
    def NullableNot(self) -> NullableBoolean:
        return NullableBoolean.Null if self == NullableBoolean.Null else self.Not()

def ToNullableBool(value: NullableBoolean) -> bool|None:
    match value:
        case NullableBoolean.Null:
            return None
        case NullableBoolean.BoolFalse:
            return False
        case NullableBoolean.BoolTrue:
            return True
    
    return ValueError(value)
def ToNullableBoolean(value: bool|None) -> NullableBoolean:
    if value is None:
        return NullableBoolean.Null
    
    if isinstance(value, bool): # type: ignore
        return NullableBoolean.BoolTrue if value else NullableBoolean.BoolFalse
    
    raise ValueError(f"value must be True, False or None. value is: {type(value)}", value)

class Endianness(Enum):
    Null = 0
    Little = 1
    Big = 2

class Sign(Enum):
    Signed = 1
    Unsigned = 2
    Float = 3

class BitDepthLevel(Enum):
    One = 8
    Two = 16
    Three = 32
    Four = 64

class IDisposable(IInterface):
    def __init__(self):
        super().__init__()
    
    def Initialize(self) -> None:
        pass

    @final
    def __enter__(self) -> Self:
        self.Initialize()
        
        return self
    
    @abstractmethod
    def Dispose(self) -> None:
        pass
    
    @final
    def __exit__(self, exc_type: type[Exception], exc_value: Exception, traceback: TracebackType) -> bool:
        self.Dispose()
        
        return False

class IStringable(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ToString(self) -> str:
        pass

    @final
    def __str__(self) -> str:
        return self.ToString()

def Not(value: bool|None) -> bool|None:
    return None if value is None else not value

def TryConvertToInt(value: object) -> int|None:
    try:
        return int(value) # type: ignore
    except ValueError:
        return None

def ReadInt(message: str, errorMessage: str = "Invalid value; an integer is expected.") -> int:
    def read() -> int|None:
        return TryConvertToInt(input(message))
        
    value: int|None = read()
    
    while value is None:
        print(errorMessage)
        
        value = read()
    
    return value

def AskConfirmation(message: str, info: str = " [y]/any other key: ", value: str = "y") -> bool:
    return input(message + info) == value