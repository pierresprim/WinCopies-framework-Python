from typing import Callable, Type
from enum import Enum

def Throw(errorMessage: str|None = "Invalid operation.") -> None:
    raise AssertionError(errorMessage)

def __EnsureFalse(condition: bool, errorMessage) -> None:
    if condition: Throw(errorMessage)
def __EnsureTrue(condition: bool, errorMessage) -> None:
    __EnsureFalse(not condition, errorMessage)

def __TryEnsure(condition: bool, errorMessage: str, action: Callable[[bool, str], None]) -> bool:
    if condition is bool:
        action(condition, errorMessage)

        return True
    
    return False
def __Ensure(condition: bool, errorMessage: str, action: Callable[[bool, str], None]) -> None:
    if not __TryEnsure(condition, errorMessage, action):
        raise ValueError(condition)

def EnsureFalse(condition: bool, errorMessage: str|None = "Invalid operation.") -> None:
    __Ensure(condition, errorMessage, __EnsureFalse)
def EnsureTrue(condition: bool, errorMessage: str|None = "Invalid operation.") -> None:
    __Ensure(condition, errorMessage, __EnsureTrue)

def __EnsureValue(value: object|None, errorMessage, action: Callable[[bool, str], None]) -> None:
    action(value is None, errorMessage)

def EnsureNone(value: object|None, errorMessage: str|None = "value must be None.") -> None:
    __EnsureValue(value, errorMessage, EnsureTrue)
def EnsureValue(value: object|None, errorMessage: str|None = "value must not be None.") -> None:
    __EnsureValue(value, errorMessage, EnsureFalse)

def EnsureNone(value: object|None, errorMessage: str|None = "value must be None.") -> bool:
    __EnsureValue(value, errorMessage, EnsureTrue)
def EnsureValue(value: object|None, errorMessage: str|None = "value must not be None.") -> bool:
    __EnsureValue(value, errorMessage, EnsureFalse)

def TryEnsureFalse(condition: bool, errorMessage: str|None = "Invalid operation.") -> bool:
    return __TryEnsure(condition, errorMessage, __EnsureFalse)
def TryEnsureTrue(condition: bool, errorMessage: str|None = "Invalid operation.") -> bool:
    return __TryEnsure(condition, errorMessage, __EnsureTrue)

def EnsureSubclass[T](c: Type, t: Type[T], errorMessage: str|None = "c must be a subclass of t.") -> None:
    EnsureTrue(issubclass(c, t), errorMessage)
def EnsureEnum(e: Type) -> None:
    EnsureSubclass(e, Enum, "e must be an enum.")