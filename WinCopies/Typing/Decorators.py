from __future__ import annotations

from typing import final, Self

from WinCopies.Assertion import Throw
from WinCopies.Typing.Delegate import Function

class MetaSingleton[T](type):
    def __init__(cls, *args, **kwargs):
        cls.__instance: T|None = None

        super().__init__(*args, **kwargs)
    
    def _GetInstance(cls) -> T|None:
        return cls.__instance
    
    def _WhenExisting(cls, *_, **__) -> None:
        Throw("Singleton class has already been instantiated.")
    def _WhenNew(cls, *args, **kwargs) -> None:
        cls.__instance = super().__call__(*args, **kwargs)
    
    def __call__(cls, *args, **kwargs):
        cls._WhenNew(*args, **kwargs) if cls.__instance is None else cls._WhenExisting(*args, **kwargs)
        
        return cls.__instance
class MetaMultiInitializationSingleton[T](MetaSingleton[T]):
    def _WhenExisting(cls, *args, **kwargs) -> None:
        cls._GetInstance().__init__(*args, **kwargs)

class Singleton[T: Self](metaclass=MetaSingleton[T]):
    @classmethod
    def _GetInstance(cls) -> T|None:
        return cls.__class__._GetInstance(cls)
class MultiInitializationSingleton[T: Self](metaclass=MetaMultiInitializationSingleton[T]):
    @classmethod
    def _GetInstance(cls) -> T|None:
        return cls.__class__._GetInstance()

def GetSingletonInstanceProvider[T: Singleton](t: type[T], *args, **kwargs) -> Function[T]:
    t(*args, **kwargs)

    return lambda: t._GetInstance()

class Static:
    def _Throw():
        raise TypeError('Static class cannot be instantiated.')
    
    @final
    def __new__(cls):
        Static._Throw()
class MetaStatic(type):
    def __call__(cls):
        cls.__new__ = Static._Throw()

def static(cls):
    cls.__new__ = lambda _: Static._Throw()
    
    return cls

def constant(f):
    def fget(self):
        return f()
    def fset(self, value):
        raise TypeError
    return property(fget, fset)