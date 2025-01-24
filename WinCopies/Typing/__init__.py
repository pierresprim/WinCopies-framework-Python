from collections.abc import Iterable
from inspect import stack, FrameInfo
from os import path
from typing import List, Type

from WinCopies.Delegates import Self
from WinCopies.Typing.Delegate import Converter, Selector

def __IsDirectCall(index: int, selector: Selector[str]) -> bool|None:
    frames: List[FrameInfo] = stack()

    nextIndex: int = index + 1

    if len(frames) > nextIndex:
        def getName(index: int) -> str:
            selector(frames[index][1])
        
        return getName(index) == getName(nextIndex)
    
    else:
        return None
def __AssertDirectCall(index: int, selector: Converter[int, bool|None]) -> None:
    result: bool|None = selector(index)

    if result is bool:
        assert(result, "Invalid operation.")

def __IsDirectModuleCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.basename)
def __IsDirectPackageCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.dirname)

def IsDirectModuleCall() -> bool|None:
    return __IsDirectModuleCall(3)
def AssertIsDirectModuleCall() -> None:
    __AssertDirectCall(4, __IsDirectModuleCall)

def IsDirectPackageCall() -> bool|None:
    return __IsDirectPackageCall(3)
def AssertIsDirectPackageCall() -> None:
    __AssertDirectCall(4, __IsDirectPackageCall)

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

class Static(type):
  def _Throw():
      raise TypeError('Static classes cannot be instantiated.')
  
  def __new__(cls):
      Static._Throw()

def static(cls):
    cls.__new__ = Static._Throw

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