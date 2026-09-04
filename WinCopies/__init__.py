# -*- coding: utf-8 -*-
"""
WinCopies Framework

Architecture-first Python framework.
"""

import sys

__version__ = "0.1.0"
__author__ = "Pierre Sprimont"
__python_requires__ = ">=3.12"

_MIN_VERSION = (3, 12)
if sys.version_info < _MIN_VERSION:
    raise RuntimeError(
        f"WinCopies requires Python {_MIN_VERSION[0]}.{_MIN_VERSION[1]}+. "
        f"You are using Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}.")

from abc import abstractmethod, ABC
from types import TracebackType
from typing import final, Self

class IInterface:
    def __init__(self) -> None: pass

class Abstract(ABC, IInterface):
    def __init__(self) -> None: super().__init__()

class IDisposableAbstract(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Dispose(self) -> None:
        ...
class IDisposableBase(IDisposableAbstract):
    def __init__(self) -> None: super().__init__()
    
    def Initialize(self) -> None:
        pass
class IDisposable(IDisposableBase):
    def __init__(self) -> None: super().__init__()
    
    def _OnExiting(self, excType: type[Exception]|None, exc: Exception|None, traceback: TracebackType|None) -> bool|None:
        return False

    @final
    def __enter__(self) -> Self:
        self.Initialize()
        
        return self
    
    @final
    def __exit__(self, exc_type: type[Exception]|None, exc_value: Exception|None, traceback: TracebackType|None) -> bool:
        result: bool|None = self._OnExiting(exc_type, exc_value, traceback)

        if result is None: return False

        self.Dispose()

        return result

class IInvalidatable(IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def Invalidate(self) -> None:
        ...

class IStringable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def ToString(self) -> str:
        ...

    @final
    def __str__(self) -> str: return self.ToString()

def IsTrue(value: bool|None) -> bool: return value is not False

def IsTruthy(value: bool|None) -> bool: return value is True
def IsFalsy(value: bool|None) -> bool: return value is not True

def Not(value: bool|None) -> bool|None: return None if value is None else not value

def TryConvertToInt(value: object) -> int|None:
    try: return int(value) # type: ignore[no-any-return, call-overload]
    except ValueError: return None