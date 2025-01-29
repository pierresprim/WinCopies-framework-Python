from typing import final

from WinCopies.Assertion import Throw

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