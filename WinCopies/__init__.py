# -*- coding: utf-8 -*-
"""
Created on Fri May 26 14:21:00 2023

@author: Pierre Sprimont
"""

from __future__ import annotations

from abc import abstractmethod, ABC
from enum import Enum
from types import TracebackType
from typing import final, Callable, Self

from WinCopies.Typing.Delegate import Action, Predicate

class IBooleanable(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ToBool(self) -> bool:
        pass
class INullableBooleanable(ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def ToNullableBoolean(self) -> NullableBoolean:
        pass
    
    @abstractmethod
    def ToNullableBool(self) -> bool|None:
        return ToNullableBool(self.ToNullableBoolean())

class NullableBoolean(Enum):
    BoolFalse = -1
    Null = 0
    BoolTrue = 1

    def __bool__(self) -> bool:
        return self > 0
    
    def Not(self) -> Self:
        return not self

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
    
    if isinstance(value, bool):
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

class IDisposable(ABC):
    def __init__(self):
        super().__init__()
    
    @final
    def __enter__(self) -> Self:
        return self
    
    @abstractmethod
    def Dispose(self) -> None:
        pass
    
    @final
    def __exit__(self, exc_type: type[Exception], exc_value: Exception, traceback: TracebackType) -> bool:
        self.Dispose()
        
        return False

class IStringable(ABC):
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
        return int(value)
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

def AskInt(message: str, predicate: Predicate[int], errorMessage: str = "The value is out of range."):
    value: int = 0
    
    def loop() -> int:
        return ReadInt(message)
    
    value = loop()
    
    while predicate(value):
        print(errorMessage)
        
        value = loop()
    
    return value

def AskConfirmation(message: str, info: str = " [y]/any other key: ", value: str = "y") -> bool:
    return input(message + info) == value

def Process(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    while AskConfirmation(message, info, value):
        action()

def DoProcess(action: Action, message: str = "Continue?", info: str = " [y]/any other key: ", value: str = "y"):
    action()
    
    Process(action, message, info, value)

def TryPredicate(predicate: Predicate[Exception], action: Action) -> bool|None:
    ok: bool = True
    _predicate: Predicate[Exception]

    def __predicate(e: Exception) -> bool:
        nonlocal ok
        nonlocal _predicate

        if predicate(e):
            ok = False
            _predicate = predicate

            return True
        
        return False
    
    _predicate = __predicate
    
    while True:
        try:
            action()

        except Exception as e:
            if _predicate(e):
                continue
                
            return None
        
        break

    return ok
def Try(action: Action, onError: Callable[[Exception], None], func: Callable[[], bool]) -> bool|None:
    def _onError(e: Exception) -> bool:
        onError(e)
        
        return func()
    
    return TryPredicate(_onError, action)
def TryMessage(action: Action, onError: Callable[[Exception], None], message: str = "Continue?") -> bool|None:
    return Try(action, onError, lambda: AskConfirmation(message))