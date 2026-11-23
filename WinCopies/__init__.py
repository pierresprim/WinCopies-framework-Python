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

class _IInitializable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    def Initialize(self) -> None:
        pass

class IDisposableAbstract(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Dispose(self) -> None:
        ...
class IDisposableBase(IDisposableAbstract, _IInitializable):
    def __init__(self) -> None: super().__init__()

class IContextManager(_IInitializable):
    """
    Lets an object be used in a with statement, whose exit runs two steps that derived types extend.

    __enter__ initializes the object and returns it. __exit__ runs _OnExiting, then _OnExited unless _OnExiting returned None. Neither can be overridden, so that a derived type only extends these two steps.
    """
    def __init__(self) -> None: super().__init__()
    
    def _OnExiting(self, excType: type[Exception]|None, exc: Exception|None, traceback: TracebackType|None) -> bool|None:
        """
        Runs the first step of the exit of a with statement.

        Args:
            excType: The type of the exception raised in the block, or None if the block ended without one.
            exc: The exception raised in the block, or None.
            traceback: The traceback of the exception raised in the block, or None.

        Returns:
            - None to end the exit without running _OnExited, and without suppressing the exception.
            - True or False to run _OnExited with this value.
        """
        return False

    def _OnExited(self, result: bool) -> bool:
        """
        Runs the second step of the exit of a with statement, once _OnExiting returned a value.

        Args:
            result: The value that _OnExiting returned.

        Returns:
            Whether the exception raised in the block, if any, is suppressed.
        """
        return result

    @final
    def __enter__(self) -> Self:
        self.Initialize()
        
        return self
    
    @final
    def __exit__(self, exc_type: type[Exception]|None, exc_value: Exception|None, traceback: TracebackType|None) -> bool:
        result: bool|None = self._OnExiting(exc_type, exc_value, traceback)

        return False if result is None else self._OnExited(result)
class IDisposable(IContextManager, IDisposableBase):
    def __init__(self) -> None: super().__init__()

    def _OnExited(self, result: bool) -> bool:
        """
        Disposes the object at the exit of a with statement.

        Args:
            result: The value that _OnExiting returned.

        Returns:
            The value that _OnExiting returned, which tells whether the exception raised in the block, if any, is suppressed.
        """
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