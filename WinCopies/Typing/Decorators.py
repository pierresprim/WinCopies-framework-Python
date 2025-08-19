from __future__ import annotations

from typing import final

from WinCopies.Assertion import Throw
from WinCopies.Typing.Delegate import Function

class MetaSingleton(type):
    def __init__(cls, *args: object, **kwargs: object):
        cls.__instance: object|None = None

        super().__init__(*args, **kwargs)
    
    def _GetInstance(cls) -> object|None:
        return cls.__instance
    
    def _WhenExisting(cls, *_: object, **__: object) -> None:
        Throw("Singleton class has already been instantiated.")
    def _WhenNew(cls, *args: object, **kwargs: object) -> None:
        cls.__instance = super().__call__(*args, **kwargs)
    
    def __call__(cls, *args: object, **kwargs: object):
        cls._WhenNew(*args, **kwargs) if cls.__instance is None else cls._WhenExisting(*args, **kwargs)
        
        return cls.__instance
class MetaMultiInitializationSingleton(MetaSingleton):
    def _WhenExisting(cls, *args: object, **kwargs: object) -> None:
        cls._GetInstance().__init__(*args, **kwargs)

class Singleton(metaclass=MetaSingleton):
    def __init__(self):
        pass
    
    @classmethod
    def _GetInstance(cls) -> object|None:
        return cls.__class__._GetInstance(cls) # type: ignore
class MultiInitializationSingleton(metaclass=MetaMultiInitializationSingleton):
    @classmethod
    def _GetInstance(cls) -> object|None:
        return cls.__class__._GetInstance()

def GetSingletonInstanceProvider[T: Singleton](t: type[T], *args: object, **kwargs: object) -> Function[T]:
    t(*args, **kwargs)

    return lambda: t._GetInstance() # type: ignore

class Static:
    @staticmethod
    def Throw():
        raise TypeError('Static class cannot be instantiated.')
    
    @final
    def __new__(cls):
        Static.Throw()
class StaticMeta(type):
    def __call__(cls):
        cls.__new__ = Static.Throw()

def static(cls):
    cls.__new__ = lambda _: Static.Throw()
    
    return cls

def constant(f):
    def fget(self):
        return f()
    def fset(self, value):
        raise TypeError
    return property(fget, fset)