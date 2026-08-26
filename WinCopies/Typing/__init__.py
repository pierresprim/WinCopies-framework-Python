from __future__ import annotations

from abc import abstractmethod, ABCMeta
from decimal import Decimal as decimal
from enum import Enum
from typing import final, overload, Any, Type as SystemType

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Typing.Delegate import Converter

type NumericalValue = int|float|decimal

class ErrorBase(Exception, Abstract):
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

def GetUnexpectedError() -> InvalidOperationError:
    return InvalidOperationError("An unexpected error occurred.")

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

class INullableValue[T](INullable[T]):
    __slots__ = ()

    @abstractmethod
    def SetValue(self, value: T) -> None:
        ...
class INullableItem[T](INullableValue[T]):
    __slots__ = ()

    @abstractmethod
    def UnsetValue(self) -> None:
        ...

    @abstractmethod
    def AsReadOnly(self) -> INullable[T]:
        ...

class _NullableValue[T](INullable[T], metaclass=ABCMeta):
    __slots__ = ()

class _Nullable[T](_NullableValue[T]):
    __slots__ = ("__value",)
    
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value

    def _SetValue(self, value: T) -> None:
        self.__value = value
    
    def HasValue(self) -> bool: return True
    def GetValue(self) -> T: return self.__value
class _NullValue[T](_NullableValue[T]):
    __slots__ = ()
    
    def HasValue(self) -> bool: return False
    def GetValue(self) -> T: raise InvalidOperationError("No value available.")

__nullValue: _NullValue[Any] = _NullValue[Any]()

class _ReadOnlyNullableValue[T](_NullableValue[T]):
    __slots__ = ("__value",)
    
    def __init__(self, value: NullableItem[T]) -> None:
        super().__init__()

        self.__value: NullableItem[T] = value
    
    def HasValue(self) -> bool: return self.__value.HasValue()
    def GetValue(self) -> T: return self.__value.GetValue()

class _INullableValueUpdater[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def SetValue(self, value: T) -> None:
        ...
    @abstractmethod
    def UnsetValue(self) -> None:
        ...

class NullableValue[T](_Nullable[T], INullableValue[T]):
    __slots__ = ()
    
    def __init__(self, value: T) -> None: super().__init__(value)

    @final
    def SetValue(self, value: T) -> None: self._SetValue(value)
@final
class _NullItem[T](_NullValue[T], INullableValue[T]):
    __slots__ = ()

    def SetValue(self, value: T) -> None: raise InvalidOperationError("No value to update.")

class NullableItem[T](_NullableValue[T], INullableItem[T]):
    @final
    class _NullableValueInitializer[_T](Abstract, _INullableValueUpdater[_T]):
        def __init__(self, value: NullableItem[_T]) -> None:
            super().__init__()

            self.__value: NullableItem[_T] = value

        def SetValue(self, value: _T) -> None: self.__value._SetValue(NullableValue[_T](value))
        def UnsetValue(self) -> None: pass
    @final
    class _NullableValueUpdater[_T](Abstract, _INullableValueUpdater[_T]):
        def __init__(self, value: NullableItem[_T]) -> None:
            super().__init__()

            self.__value: NullableItem[_T] = value

        def SetValue(self, value: _T) -> None: self.__value._GetValue().SetValue(value)
        def UnsetValue(self) -> None: self.__value._UnsetValue()
    
    # __slots__ = ("__value", "__readOnly", "__updater")
    
    def __init__(self, value: INullableValue[T]|None = None) -> None:
        super().__init__()

        _value, updater = self.__GetInitialValue(value)

        self.__value: INullableValue[T] = _value
        self.__readOnly: INullable[T] = _ReadOnlyNullableValue[T](self)

        self.__updater: _INullableValueUpdater[T] = updater

    @final
    def __GetInitializer(self) -> _INullableValueUpdater[T]:
        return NullableItem._NullableValueInitializer[T](self)
    @final
    def __GetUpdater(self) -> _INullableValueUpdater[T]:
        return NullableItem._NullableValueUpdater[T](self)

    @final
    def __GetInitialValue(self, value: INullableValue[T]|None) -> tuple[INullableValue[T], _INullableValueUpdater[T]]:
        return (_GetNullValue(), self.__GetInitializer()) if value is None else (value, self.__GetUpdater())

    @final
    def _GetValue(self) -> INullableValue[T]:
        return self.__value
    
    @final
    def _SetValue(self, value: INullableValue[T]) -> None:
        self.__value = value
        self.__updater = self.__GetUpdater()
    @final
    def _UnsetValue(self) -> None:
        self.__value = _GetNullValue()
        self.__updater = self.__GetInitializer()

    @final
    def HasValue(self) -> bool: return self.__value.HasValue()
    @final
    def GetValue(self) -> T: return self.__value.GetValue()

    @final
    def SetValue(self, value: T) -> None: self.__updater.SetValue(value)
    @final
    def UnsetValue(self) -> None: self.__updater.UnsetValue()

    @final
    def AsReadOnly(self) -> INullable[T]: return self.__readOnly

__nullItem: INullableValue[Any] = _NullItem[Any]()

def _GetNullValue[T]() -> INullableValue[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __nullItem

def GetNullable[T](value: T) -> INullable[T]:
    return _Nullable[T](value)
def GetNullValue[T]() -> INullable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __nullValue

def TryGetValue[T](value: INullable[T]|None) -> T|None:
    return None if value is None else value.TryGetValue()

def GetNullableValue[T](value: T|None) -> INullable[T]:
    return GetNullValue() if value is None else GetNullable(value)

def GetNullableItem[T](value: T|None) -> INullableItem[T]:
    return CreateNullableItem(None if value is None else NullableValue[T](value))

def CreateNullableItem[T](value: INullableValue[T]|None = None) -> INullableItem[T]:
    return NullableItem[T](value)

def HasValue[T](value: INullable[T]|None) -> bool:
    return value is not None and value.HasValue()

def TryGetValueAs[TValue, TDefault](type: SystemType[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: SystemType[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)

class IEnumBase(IStringable):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetEnumValue(self) -> Enum:
        ...

    def ToString(self) -> str: return str(self.GetEnumValue())
class IEnum[T: Enum](IEnumBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetEnumValue(self) -> T:
        ...