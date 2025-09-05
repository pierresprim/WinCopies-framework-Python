from abc import abstractmethod
from typing import final, Type

import WinCopies

from WinCopies import IInterface, IStringable

class IStruct[T](IInterface):
    def __init__(self):
        pass
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
class Struct[T](IStruct[T]):
    def __init__(self, value: T):
        super().__init__()

        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    def SetValue(self, value: T) -> None:
        self.__value = value

class InvalidOperationError(Exception):
    def __init__(self, *args: object):
        super().__init__(*args)

class IEquatable[T](IInterface):
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

def GetDisposedError() -> InvalidOperationError:
    raise InvalidOperationError("The current table has been disposed.")

class IDisposable(WinCopies.IDisposable):
    def __init__(self):
        super().__init__()

    @final
    def _Throw(self) -> None:
        raise GetDisposedError()

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self):
        super().__init__()

class __IGenericConstraint[TContainer, TInterface](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsContainer(self, container: TContainer) -> TInterface:
        pass

class IGenericConstraint[TContainer, TInterface](__IGenericConstraint[TContainer, TInterface]):
    def __init__(self):
        super().__init__()
    
    @final
    def _TryAsContainer(self, container: TContainer|None) -> TInterface|None:
        return None if container is None else self._AsContainer(container)

class GenericConstraint[TContainer, TInterface](IGenericConstraint[TContainer, TInterface]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _GetContainer(self) -> TContainer:
        pass
    @final
    def _GetInnerContainer(self) -> TInterface:
        return self._AsContainer(self._GetContainer())

class IGenericConstraintImplementation[T](__IGenericConstraint[T, T]):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsContainer(self, container: T) -> T:
        return container

class INullable[T](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def HasValue(self) -> bool:
        pass

    @abstractmethod
    def GetValue(self) -> T:
        pass
    @final
    def TryGetValue[U](self, default: U|None = None) -> T|U|None:
        return self.GetValue() if self.HasValue() else default

@final
class __Nullable[T](INullable[T]):
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    def HasValue(self) -> bool:
        return True
    def GetValue(self) -> T:
        return self.__value
class __NullValue[T](INullable[T]):
    def __init__(self):
        super().__init__()
    
    def HasValue(self) -> bool:
        return False
    def GetValue(self) -> T:
        raise InvalidOperationError()

__nullValue: __NullValue = __NullValue() # type: ignore

def GetNullable[T](value: T) -> INullable[T]:
    return __Nullable[T](value)
def GetNullValue[T]() -> INullable[T]: # type: ignore
    return __nullValue # type: ignore

def TryGetValueAs[TValue, TDefault](type: Type[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: Type[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)