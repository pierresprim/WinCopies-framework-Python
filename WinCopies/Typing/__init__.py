from abc import abstractmethod, ABC
from collections.abc import Iterable
from inspect import stack, FrameInfo
from os import path
from typing import final, List, Type

from WinCopies import IDisposable, IStringable
from WinCopies.Assertion import TryEnsureTrue
from WinCopies.Typing.Delegate import Converter, Selector

class IStruct[T](ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
class Struct[T](IStruct[T]):
    def __init__(self, value: T):
        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    def SetValue(self, value: T) -> None:
        self.__value = value

class IEquatable[T](ABC):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: T|object) -> bool:
        pass
    
    @final
    def __eq__(self, value: object) -> bool:
        return self.Equals(value)
class IEquatableObject[T](IEquatable[T]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        pass

    @final
    def __hash__(self) -> int:
        return self.Hash()

class IObject[T](IEquatableObject[T], IStringable):
    def __init__(self):
        super().__init__()

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self):
        super().__init__()

class __IGenericConstraint[TContainer, TInterface](ABC):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsContainer(self, container: TContainer) -> TInterface:
        pass

class IGenericConstraint[TContainer, TInterface](__IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @final
    def _TryAsContainer(self, container: TContainer|None) -> TInterface|None:
        return None if container is None else self._AsContainer(container)
class IInvariantGenericConstraint[TContainer, TInterface](IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _AsInterface(self, interface: TInterface) -> TContainer:
        pass
    @final
    def _TryAsInterface(self, interface: TInterface|None) -> TContainer|None:
        return None if interface is None else self._AsInterface(interface)

class GenericConstraint[TContainer, TInterface](IGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def _GetContainer(self) -> TContainer:
        pass
    @final
    def _GetInnerContainer(self) -> TInterface:
        return self._AsContainer(self._GetContainer())
class InvariantGenericConstraint[TContainer, TInterface](GenericConstraint[TContainer, TInterface], IInvariantGenericConstraint[TContainer, TInterface]):
    def __init__(self) -> None:
        super().__init__()

class IGenericConstraintImplementation[T](__IGenericConstraint[T, T]):
    def __init__(self) -> None:
        super().__init__()
    
    def _AsContainer(self, container: T) -> T:
        return container

def __IsDirectCall(index: int, selector: Selector[str]) -> bool|None:
    frames: List[FrameInfo] = stack()

    nextIndex: int = index + 1

    if len(frames) > nextIndex:
        def getName(index: int) -> str:
            return selector(frames[index][1])
        
        return getName(index) == getName(nextIndex)
    
    else:
        return None
def __EnsureDirectCall(index: int, selector: Converter[int, bool|None]) -> None:
    if not TryEnsureTrue(selector(index) == True):
        raise ValueError(index)

def __IsDirectModuleCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.basename)
def __IsDirectPackageCall(index: int) -> bool|None:
    return __IsDirectCall(index, path.dirname)

def IsDirectModuleCall() -> bool|None:
    return __IsDirectModuleCall(3)
def EnsureDirectModuleCall() -> None:
    __EnsureDirectCall(4, __IsDirectModuleCall)

def IsDirectPackageCall() -> bool|None:
    return __IsDirectPackageCall(3)
def EnsureDirectPackageCall() -> None:
    __EnsureDirectCall(4, __IsDirectPackageCall)

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

class InvalidOperationError(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)