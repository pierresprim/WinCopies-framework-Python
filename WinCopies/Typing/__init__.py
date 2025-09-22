from __future__ import annotations

from abc import abstractmethod
from typing import final, Callable, Type

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

class IEquatableValue(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: object) -> bool:
        pass
    
    @final
    def __eq__(self, value: object) -> bool:
        return self.Equals(value)
class IEquatableItem(IEquatableValue):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        pass

    @final
    def __hash__(self) -> int:
        return self.Hash()

class IEquatable[T](IEquatableValue):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: T|object) -> bool:
        pass
class IEquatableObject[T](IEquatable[T], IEquatableItem):
    def __init__(self):
        super().__init__()

class IItem(IEquatableItem, IStringable):
    def __init__(self):
        super().__init__()
class IObject[T](IEquatableObject[T], IItem):
    def __init__(self):
        super().__init__()

class IString(IObject['IString']):
    def __init__(self):
        super().__init__()
class String(IString):
    def __init__(self, value: str):
        super().__init__()

        self.__value: str = value
    
    def Equals(self, item: IString|object) -> bool:
        def equals(item: str) -> bool:
            return self.ToString() == item
        
        return (isinstance(item, IString) and equals(item.ToString())) or (isinstance(item, str) and equals(item))
    
    def Hash(self) -> int:
        return hash(self.ToString())
    
    def ToString(self) -> str:
        return self.__value

def GetDisposedError() -> InvalidOperationError:
    return InvalidOperationError("The current object has been disposed.")

class IDisposable(WinCopies.IDisposable):
    def __init__(self):
        super().__init__()

    @final
    def _Throw(self) -> None:
        raise GetDisposedError()

class IDisposableInfo(IDisposable):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def IsDisposed(self) -> bool:
        pass

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self):
        super().__init__()

class __IGenericConstraint[TContainer, TInterface](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsContainer(self, container: TContainer) -> TInterface:
        pass
class __IGenericSpecializedConstraint[TContainer, TOverridden, TInterface, TSpecialized](__IGenericConstraint[TContainer, TInterface]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def _AsSpecialized(self, container: TOverridden) -> TSpecialized:
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
class GenericSpecializedConstraint[TContainer, TInterface, TSpecialized](GenericConstraint[TContainer, TInterface], __IGenericSpecializedConstraint[TContainer, TContainer, TInterface, TSpecialized]):
    def __init__(self):
        super().__init__()

    @final
    def _GetSpecializedContainer(self) -> TSpecialized:
        return self._AsSpecialized(self._GetContainer())

class IGenericConstraintImplementation[T](__IGenericConstraint[T, T]):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsContainer(self, container: T) -> T:
        return container
class IGenericSpecializedConstraintImplementation[TInterface, TSpecialized](IGenericConstraintImplementation[TInterface], __IGenericSpecializedConstraint[TInterface, TSpecialized, TInterface, TSpecialized]):
    def __init__(self):
        super().__init__()
    
    @final
    def _AsSpecialized(self, container: TSpecialized) -> TSpecialized:
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
    def Convert[TOut](self, converter: Callable[[T], TOut]) -> TOut:
        return converter(self.GetValue())
    @final
    def TryConvert[U, TOut](self, converter: Callable[[T], TOut], default: U|None = None) -> TOut|U|None:
        return self.Convert(converter) if self.HasValue() else default
    
    @final
    def ConvertToNullable[TOut](self, converter: Callable[[T], TOut]) -> INullable[TOut]:
        return GetNullable(converter(self.GetValue()))
    @final
    def TryConvertToNullable[TOut](self, converter: Callable[[T], TOut]) -> INullable[TOut]:
        return self.ConvertToNullable(converter) if self.HasValue() else GetNullValue()

@final
class __Nullable[T](INullable[T]):
    def __init__(self, value: T):
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

class __IDisposableProviderItem[T: IDisposableInfo](IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetItem(self) -> T:
        pass

    @abstractmethod
    def IsDisposed(self) -> bool:
        pass

    @abstractmethod
    def Dispose(self) -> __IDisposableProviderItem[T]:
        pass
@final
class __DisposedItem[T: IDisposableInfo](__IDisposableProviderItem[T]):
    def __init__(self):
        super().__init__()
    
    def GetItem(self) -> T:
        raise GetDisposedError()

    def IsDisposed(self) -> bool:
        return True

    def Dispose(self) -> __IDisposableProviderItem[T]:
        return self

__disposedItem = __DisposedItem() # type: ignore

@final
class __DisposableProviderItem[T: IDisposableInfo](__IDisposableProviderItem[T]):
    def __init__(self, item: T):
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T:
        return self.__item

    def IsDisposed(self) -> bool:
        return self.__item.IsDisposed()
    
    def Dispose(self) -> __IDisposableProviderItem[T]:
        self.__item.Dispose()
        
        return __disposedItem # type: ignore

class IDisposableProvider[T: IDisposableInfo](IDisposableInfo):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def _GetItem(self) -> T:
        pass
    
    @final
    def GetItem(self) -> T:
        if self.IsDisposed():
            raise GetDisposedError()
        
        return self._GetItem()
    @final
    def TryGetItem(self) -> INullable[T]:
        return GetNullValue() if self.IsDisposed() else GetNullable(self._GetItem())
class DisposableProvider[T: IDisposableInfo](IDisposableProvider[T]):
    def __init__(self, item: T):
        super().__init__()

        self.__item: __IDisposableProviderItem[T] = __DisposableProviderItem[T](item)
    
    @final
    def _GetItem(self) -> T:
        return self.__item.GetItem()
    
    @final
    def IsDisposed(self) -> bool:
        return self.__item.IsDisposed()
    
    @final
    def Dispose(self) -> None:
        self.__item = self.__item.Dispose()

def TryGetValueAs[TValue, TDefault](type: Type[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: Type[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)