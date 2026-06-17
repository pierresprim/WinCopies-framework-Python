from __future__ import annotations

from abc import abstractmethod, ABCMeta
from decimal import Decimal as decimal
from enum import Enum
from typing import final, overload, Type as SystemType

from WinCopies import IInterface, IDisposable as IDisposableBase, Abstract
from WinCopies.Typing.Delegate import Converter

type NumericalValue = int|float|decimal

class ErrorBase(Exception):
    def __init__(self, *args: object) -> None: super().__init__(*args)
    
    @abstractmethod
    def GetMessage(self) -> str:
        ...
    
    def __str__(self) -> str: return self.GetMessage()
class Error(ErrorBase):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)

        self.__message: str = message # 'args' can be reassigned after construction, so the message is kept here as a stable source for GetMessage().
    
    @final
    def GetMessage(self) -> str: return self.__message

class InvalidOperationError(Error):
    def __init__(self, message: str, *args: object) -> None: super().__init__(message, *args)

def GetGenericError() -> InvalidOperationError:
    return InvalidOperationError("Could not perform the requested action.")

def GetDisposedError() -> InvalidOperationError:
    return InvalidOperationError("The current object has been disposed.")

class IDisposable(IDisposableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def _Throw(self) -> None: raise GetDisposedError()

class IDisposableInfo(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsDisposed(self) -> bool:
        ...

class INullable[T]:
    __slots__ = ()

    @abstractmethod
    def HasValue(self) -> bool:
        ...

    @abstractmethod
    def GetValue(self) -> T:
        ...
    
    @final
    def TryGetValueOrDefault[U](self, default: U) -> T|U:
        return self.GetValue() if self.HasValue() else default
    @final
    def TryGetValue(self) -> T|None:
        return self.TryGetValueOrDefault(None)
    
    @final
    def Convert[TOut](self, converter: Converter[T, TOut]) -> TOut:
        return converter(self.GetValue())
    
    @overload
    def TryConvert[U, TOut](self, converter: Converter[T, TOut], default: U) -> TOut|U:
        ...
    @overload
    def TryConvert[TOut](self, converter: Converter[T, TOut], default: None = None) -> TOut|None:
        ...
    
    @final
    def TryConvert[U, TOut](self, converter: Converter[T, TOut], default: U|None = None) -> TOut|U|None:
        return self.Convert(converter) if self.HasValue() else default
    
    @final
    def ConvertToNullable[TOut](self, converter: Converter[T, TOut]) -> INullable[TOut]:
        return GetNullable(converter(self.GetValue()))
    @final
    def TryConvertToNullable[TOut](self, converter: Converter[T, TOut]) -> INullable[TOut]:
        return self.ConvertToNullable(converter) if self.HasValue() else GetNullValue()

class _NullableValue[T](INullable[T], metaclass=ABCMeta):
    __slots__ = ()

@final
class _Nullable[T](_NullableValue[T]):
    __slots__ = ('__value',)
    
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    def HasValue(self) -> bool: return True
    def GetValue(self) -> T: return self.__value
@final
class _NullValue[T](_NullableValue[T]):
    __slots__ = ()
    
    def __init__(self) -> None: super().__init__()
    
    def HasValue(self) -> bool: return False
    def GetValue(self) -> T: raise InvalidOperationError("No value available.")

__nullValue: _NullValue = _NullValue() # type: ignore

def GetNullable[T](value: T) -> INullable[T]:
    return _Nullable[T](value)
def GetNullValue[T]() -> INullable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __nullValue # pyright: ignore[reportUnknownVariableType]

def TryGetValue[T](value: INullable[T]|None) -> T|None:
    return None if value is None else value.TryGetValue()

def GetNullableValue[T](value: T|None) -> INullable[T]:
    return GetNullValue() if value is None else GetNullable(value)

def HasValue[T](value: INullable[T]|None) -> bool:
    return value is not None and value.HasValue()

class _IDisposableProviderItem[T: IDisposableInfo](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetItem(self) -> T:
        ...

    @abstractmethod
    def IsDisposed(self) -> bool:
        ...

    @abstractmethod
    def Dispose(self) -> _IDisposableProviderItem[T]:
        ...
@final
class _DisposedItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self) -> None: super().__init__()
    
    def GetItem(self) -> T: raise GetDisposedError()

    def IsDisposed(self) -> bool: return True

    def Dispose(self) -> _IDisposableProviderItem[T]: return self

__disposedItem = _DisposedItem() # type: ignore

@final
class _DisposableProviderItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T: return self.__item

    def IsDisposed(self) -> bool: return self.__item.IsDisposed()
    
    def Dispose(self) -> _IDisposableProviderItem[T]:
        self.__item.Dispose()
        
        return __disposedItem # pyright: ignore[reportUnknownVariableType]

class IDisposableProvider[T: IDisposableInfo](IDisposableInfo):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetItem(self) -> T:
        ...
    
    @final
    def GetItem(self) -> T:
        if self.IsDisposed(): raise GetDisposedError()
        
        return self._GetItem()
    @final
    def TryGetItem(self) -> INullable[T]:
        return GetNullValue() if self.IsDisposed() else GetNullable(self._GetItem())
class DisposableProvider[T: IDisposableInfo](Abstract, IDisposableProvider[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: _IDisposableProviderItem[T] = _DisposableProviderItem[T](item)
    
    @final
    def _GetItem(self) -> T:
        return self.__item.GetItem()
    
    @final
    def IsDisposed(self) -> bool: return self.__item.IsDisposed()
    
    @final
    def Dispose(self) -> None: self.__item = self.__item.Dispose()

def TryGetValueAs[TValue, TDefault](type: SystemType[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: SystemType[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)

class IMonitor(IDisposable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsBusy(self) -> bool:
        ...
class Monitor(Abstract, IMonitor):
    def __init__(self) -> None:
        super().__init__()

        self.__isBusy: bool = False
    
    @final
    def Initialize(self) -> None: self.__isBusy = True
    
    @final
    def IsBusy(self) -> bool: return self.__isBusy
    
    @final
    def Dispose(self) -> None: self.__isBusy = False

class IEnum(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetEnumValue(self) -> Enum:
        ...