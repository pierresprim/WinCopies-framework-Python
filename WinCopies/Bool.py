from __future__ import annotations

from abc import abstractmethod
from typing import final

from WinCopies import IInterface
from WinCopies.Typing.Enum import IntEnum

class BooleanableEnum(IntEnum):
    def __bool__(self) -> bool: return self >= 0

class NullableBoolean(BooleanableEnum):
    BoolFalse = -1
    Null = 0
    BoolTrue = 1
    
    def Not(self) -> NullableBoolean:
        return NullableBoolean.BoolFalse if self else NullableBoolean.BoolTrue
    def NullableNot(self) -> NullableBoolean:
        return NullableBoolean.Null if self == NullableBoolean.Null else self.Not()

class IBooleanable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToBool(self) -> bool:
        ...
class INullableBooleanable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToNullableBoolean(self) -> NullableBoolean:
        ...
    
    @final
    def ToNullableBool(self) -> bool|None:
        return ToNullableBool(self.ToNullableBoolean())

def ToNullableBool(value: NullableBoolean) -> bool|None:
    match value:
        case NullableBoolean.Null: return None
        
        case NullableBoolean.BoolFalse: return False
        case NullableBoolean.BoolTrue: return True
    
    return ValueError(value)
def ToNullableBoolean(value: bool|None) -> NullableBoolean:
    match value:
        case True: return NullableBoolean.BoolTrue
        case False: return NullableBoolean.BoolFalse
        
        case _: return NullableBoolean.Null