from __future__ import annotations

from abc import abstractmethod, ABCMeta
from decimal import Decimal as decimal
from enum import Enum
from typing import final, overload, Type as SystemType

from WinCopies import IInterface, IStringable, IDisposable as IDisposableBase, Abstract
from WinCopies.Typing.Delegate import Method, Function, Converter
from WinCopies.Typing.Enum import IntEnum

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

class UnusabilityReason(IntEnum):
    Null = 0
    Discarded = 1
    Broken = 2

class DiscardReason(IntEnum):
    Null = 0
    Finalized = 1
    Disposed = 2
    Invalidated = 3

    def IsExplicit(self) -> bool:
        return self > DiscardReason.Finalized

    def ToString(self) -> str:
        return '' if self == DiscardReason.Null else self.name

class UnusableError(InvalidOperationError):
    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)

    @abstractmethod
    def GetUnusabilityReason(self) -> UnusabilityReason:
        ...

class DiscardedError(UnusableError):
    def __init__(self, message: str|None, *args: object) -> None: super().__init__(f"The current object has been {self.GetDiscardReason().ToString().lower()}." if message is None else message, *args)

    @final
    def GetUnusabilityReason(self) -> UnusabilityReason: return UnusabilityReason.Discarded

    @abstractmethod
    def GetDiscardReason(self) -> DiscardReason:
        ...

@final
class _DiscardedError(DiscardedError):
    def __init__(self) -> None: super().__init__("The object was discarded for unknown reason.")

    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Null

class DisposedError(DiscardedError):
    def __init__(self, *args: object) -> None: super().__init__(None, *args)

    @final
    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Disposed
class InvalidatedError(DiscardedError):
    def __init__(self, *args: object) -> None: super().__init__(None, *args)

    @final
    def GetDiscardReason(self) -> DiscardReason: return DiscardReason.Invalidated

class BrokenObjectError(UnusableError):
    def __init__(self, message: str, *args: object) -> None: super().__init__(message, *args)

    @final
    def GetUnusabilityReason(self) -> UnusabilityReason: return UnusabilityReason.Broken

def GetGenericError() -> InvalidOperationError:
    return InvalidOperationError("Could not perform the requested action.")

def TryGetDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> DiscardedError|None:
    match discardReason:
        case DiscardReason.Disposed: return DisposedError()
        case DiscardReason.Invalidated: return InvalidatedError()

        case _: return None

def GetDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> DiscardedError:
    e: DiscardedError|None = TryGetDiscardedError(discardReason)

    return _DiscardedError() if e is None else e

def ThrowInvalidatedError() -> None:
    raise InvalidatedError()
def ThrowDisposedError() -> None:
    raise DisposedError()
def ThrowDiscardedError(discardReason: DiscardReason = DiscardReason.Disposed) -> None:
    raise GetDiscardedError(discardReason)

class IDisposable(IDisposableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def _Throw(self) -> None: raise GetDiscardedError()

class IDiscardableInfo(IDisposableBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def IsDisposed(self) -> bool:
        ...

class IDisposableInfo(IDisposable, IDiscardableInfo):
    def __init__(self) -> None: super().__init__()

class IInvalidatable(IDisposableBase):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _Dispose(self, reason: DiscardReason) -> None:
        ...

    @final
    def Dispose(self) -> None: self._Dispose(DiscardReason.Disposed)

    @final
    def Invalidate(self) -> None: self._Dispose(DiscardReason.Invalidated)
class IInvalidatableInfo(IInvalidatable, IDiscardableInfo):
    def __init__(self) -> None: super().__init__()

class DisposableBase(Abstract, IDisposableInfo):
    def __init__(self) -> None:
        super().__init__()

        self.__dispose: Method[DiscardReason] = self.__Dispose

    def _OnDisposing(self, reason: DiscardReason) -> None:
        pass

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        pass
    
    def _Finalize(self) -> None:
        pass
    
    def __Dispose(self, reason: DiscardReason) -> None:
        if reason == DiscardReason.Null: return

        self._OnDisposing(reason)

        if reason.IsExplicit():
            self._DisposeOverride(reason)

            self.__dispose = lambda _: None

        self._Finalize()

    @final
    def _Dispose(self, reason: DiscardReason) -> None:
        dispose: Method[DiscardReason] = self.__dispose # Needed for mypy compatibility

        dispose(reason)

    @final
    def IsDisposed(self) -> bool:
        # Equality, not identity: 'self.__Dispose' builds a new bound method object on
        # each access, so 'is not' would always be True. '!=' compares __self__ and
        # __func__, which is the intended check.
        return self.__dispose != self.__Dispose
class Disposable(DisposableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def Dispose(self) -> None: self._Dispose(DiscardReason.Disposed)

class InvalidatableObjectProviderBase[T](DisposableBase, IInvalidatableInfo):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetValue(self) -> T:
        ...

    @abstractmethod
    def _SetValueProvider(self, func: Function[T]) -> None:
        ...
class InvalidatableObjectProvider[T](InvalidatableObjectProviderBase[T]):
    def __init__(self, func: Function[T]) -> None:
        super().__init__()

        self.__func: Function[T] = func

    @final
    def _GetValue(self) -> T: return self.__func()

    @final
    def _SetValueProvider(self, func: Function[T]) -> None: self.__func = func

    def _DisposeOverride(self, reason: DiscardReason) -> None:
        # A new error instance is built on each raise: re-raising a captured one would
        # chain a new traceback onto it every time, growing without bound and keeping
        # every frame — and its locals — alive. The object is typically held for the
        # lifetime of its consumer, so this would be a leak, not just noise.
        def throw(reason: DiscardReason) -> T: raise GetDiscardedError(reason)

        super()._DisposeOverride(reason)

        self._SetValueProvider(lambda: throw(reason))

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
    
    def GetItem(self) -> T: raise GetDiscardedError()

    def IsDisposed(self) -> bool: return True

    def Dispose(self) -> _IDisposableProviderItem[T]: return self

_disposedItem = _DisposedItem() # type: ignore

@final
class _DisposableProviderItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T: return self.__item

    def IsDisposed(self) -> bool: return self.__item.IsDisposed()
    
    def Dispose(self) -> _IDisposableProviderItem[T]:
        self.__item.Dispose()
        
        return _disposedItem # pyright: ignore[reportUnknownVariableType]

class IDisposableProvider[T: IDisposableInfo](IDisposableInfo):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _GetItem(self) -> T:
        ...
    
    @final
    def GetItem(self) -> T:
        if self.IsDisposed(): raise GetDiscardedError()
        
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