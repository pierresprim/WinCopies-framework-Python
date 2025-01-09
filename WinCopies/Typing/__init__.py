from typing import Iterable, Type

from WinCopies.Delegates import Self

class Singleton(type):
    __instances = {}
    
    def WhenExisting(cls, *args, **kwargs) -> None:
        pass
    def WhenNew(cls, *args, **kwargs) -> None:
        cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
    
    def __call__(cls, *args, **kwargs):
        (Singleton.WhenExisting if cls in cls.__instances else Singleton.WhenNew)(cls, args, kwargs)
            
        return cls.__instances[cls]

class MultiInitializationSingleton(Singleton):
    def WhenExisting(cls, *args, **kwargs) -> None:
        cls._instances[cls].__init__(*args, **kwargs)

def singleton(cls):
    cls.__call__ = Self
    return cls()

def constant(f):
    def fget(self):
        return f()
    def fset(self, value):
        raise TypeError
    return property(fget, fset)

def IsSubclass[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    for type in types:
        if issubclass(cls, type):
            return True
    
    return False
def IsSubclassOf[T](cls: Type[T], *types: Type[T]) -> bool:
    return IsSubclass(cls, types)

def Is[T](obj: T, types: Iterable[Type[T]]) -> bool:
    return IsSubclass(type(obj), types)
def IsOf[T](obj: T, *types: Type[T]) -> bool:
    return Is(obj, types)

def Implements[T](cls: Type[T], types: Iterable[Type[T]]) -> bool:
    for type in types:
        if not issubclass(cls, type):
            return False
    
    return True
def ImplementsAll[T](cls: Type[T], *types: Type[T]) -> bool:
    return Implements(cls, types)

def IsFrom[T](obj: T, types: Iterable[Type[T]]) -> bool:
    return Implements(type(obj), types)
def IsFromAll[T](obj: T, *types: Type[T]) -> bool:
    return IsFrom(obj, types)