from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import final, runtime_checkable, Any, Protocol, Type as SystemType

from WinCopies import IInterface, IDisposable as IDisposableBase, Abstract
from WinCopies.Typing.Delegate import Converter

class InvalidOperationError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)

class IEquatableValue(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: object) -> bool:
        pass
    
    @final
    def __eq__(self, value: object) -> bool:
        return self.Equals(value)
class IEquatableItem(IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        pass

    @final
    def __hash__(self) -> int:
        return self.Hash()

class IEquatable[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: T) -> bool:
        pass
class IEquatableObject[T](IEquatable[T|object], IEquatableValue):
    def __init__(self) -> None:
        super().__init__()

@runtime_checkable
class SupportsRichComparison(Protocol):
    """Protocol for types that support comparison operators."""
    
    def __lt__(self, other: Any, /) -> bool:
        """Less than comparison."""
        ...
    
    def __le__(self, other: Any, /) -> bool:
        """Less than or equal comparison."""
        ...
    
    def __gt__(self, other: Any, /) -> bool:
        """Greater than comparison."""
        ...
    
    def __ge__(self, other: Any, /) -> bool:
        """Greater than or equal comparison."""
        ...

class IComparableValue(IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsLessThan(self, other: object) -> bool:
        """Less than comparison."""
        pass
    
    @abstractmethod
    def IsLessThanOrEqual(self, other: object) -> bool:
        """Less than or equal comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThan(self, other: object) -> bool:
        """Greater than comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThanOrEqual(self, other: object) -> bool:
        """Greater than or equal comparison."""
        pass
    
    @final
    def __lt__(self, other: Any, /) -> bool:
        """Less than comparison."""
        return self.IsLessThan(other)
    
    @final
    def __le__(self, other: Any, /) -> bool:
        """Less than or equal comparison."""
        return self.IsLessThanOrEqual(other)
    
    @final
    def __gt__(self, other: Any, /) -> bool:
        """Greater than comparison."""
        return self.IsGreaterThan(other)
    
    @final
    def __ge__(self, other: Any, /) -> bool:
        """Greater than or equal comparison."""
        return self.IsGreaterThanOrEqual(other)
class IComparableItem(IComparableValue, IEquatableItem):
    def __init__(self) -> None:
        super().__init__()
class IComparable[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CompareTo(self, item: T) -> bool|None:
        pass
    
    @final
    def IsLessThan(self, other: T) -> bool:
        """Less than comparison."""
        return self.CompareTo(other) is False
    
    @final
    def IsLessThanOrEqual(self, other: T) -> bool:
        """Less than or equal comparison."""
        return self.CompareTo(other) is not True
    
    @final
    def IsGreaterThan(self, other: T) -> bool:
        """Greater than comparison."""
        return self.CompareTo(other) is True
    
    @final
    def IsGreaterThanOrEqual(self, other: T) -> bool:
        """Greater than or equal comparison."""
        return self.CompareTo(other) is not False
class IComparableObject[T](IComparable[T|object], IComparableValue, IEquatableObject[T]):
    def __init__(self) -> None:
        super().__init__()

def GetDisposedError() -> InvalidOperationError:
    return InvalidOperationError("The current object has been disposed.")

class IDisposable(IDisposableBase):
    def __init__(self) -> None:
        super().__init__()

    @final
    def _Throw(self) -> None:
        raise GetDisposedError()

class IDisposableInfo(IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsDisposed(self) -> bool:
        pass

class INullable[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def HasValue(self) -> bool:
        pass

    @abstractmethod
    def GetValue(self) -> T:
        pass
    
    @final
    def TryGetValueOrDefault[U](self, default: U) -> T|U:
        return self.GetValue() if self.HasValue() else default
    @final
    def TryGetValue(self) -> T|None:
        return self.TryGetValueOrDefault(None)
    
    @final
    def Convert[TOut](self, converter: Converter[T, TOut]) -> TOut:
        return converter(self.GetValue())
    @final
    def TryConvert[U, TOut](self, converter: Converter[T, TOut], default: U|None = None) -> TOut|U|None:
        return self.Convert(converter) if self.HasValue() else default
    
    @final
    def ConvertToNullable[TOut](self, converter: Converter[T, TOut]) -> INullable[TOut]:
        return GetNullable(converter(self.GetValue()))
    @final
    def TryConvertToNullable[TOut](self, converter: Converter[T, TOut]) -> INullable[TOut]:
        return self.ConvertToNullable(converter) if self.HasValue() else GetNullValue()

@final
class _Nullable[T](Abstract, INullable[T]):
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    def HasValue(self) -> bool:
        return True
    def GetValue(self) -> T:
        return self.__value
@final
class _NullValue[T](Abstract, INullable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def HasValue(self) -> bool:
        return False
    def GetValue(self) -> T:
        raise InvalidOperationError()

__nullValue: _NullValue = _NullValue() # type: ignore

def GetNullable[T](value: T) -> INullable[T]:
    return _Nullable[T](value)
def GetNullValue[T]() -> INullable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __nullValue # pyright: ignore[reportUnknownVariableType]

def TryGetValue[T](value: INullable[T]|None) -> T|None:
    return None if value is None else value.TryGetValue()

class _IDisposableProviderItem[T: IDisposableInfo](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetItem(self) -> T:
        pass

    @abstractmethod
    def IsDisposed(self) -> bool:
        pass

    @abstractmethod
    def Dispose(self) -> _IDisposableProviderItem[T]:
        pass
@final
class _DisposedItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def GetItem(self) -> T:
        raise GetDisposedError()

    def IsDisposed(self) -> bool:
        return True

    def Dispose(self) -> _IDisposableProviderItem[T]:
        return self

__disposedItem = _DisposedItem() # type: ignore

@final
class _DisposableProviderItem[T: IDisposableInfo](Abstract, _IDisposableProviderItem[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T:
        return self.__item

    def IsDisposed(self) -> bool:
        return self.__item.IsDisposed()
    
    def Dispose(self) -> _IDisposableProviderItem[T]:
        self.__item.Dispose()
        
        return __disposedItem # pyright: ignore[reportUnknownVariableType]

class IDisposableProvider[T: IDisposableInfo](IDisposableInfo):
    def __init__(self) -> None:
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
class DisposableProvider[T: IDisposableInfo](Abstract, IDisposableProvider[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: _IDisposableProviderItem[T] = _DisposableProviderItem[T](item)
    
    @final
    def _GetItem(self) -> T:
        return self.__item.GetItem()
    
    @final
    def IsDisposed(self) -> bool:
        return self.__item.IsDisposed()
    
    @final
    def Dispose(self) -> None:
        self.__item = self.__item.Dispose()

def TryGetValueAs[TValue, TDefault](type: SystemType[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: SystemType[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)

class IMonitor(IDisposable):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsBusy(self) -> bool:
        pass
class Monitor(Abstract, IMonitor):
    def __init__(self) -> None:
        super().__init__()

        self.__isBusy: bool = False
    
    @final
    def __Reset(self) -> None:
        self.__isBusy = False
    
    @final
    def Initialize(self) -> None:
        self.__isBusy = True
    
    @final
    def IsBusy(self) -> bool:
        return self.__isBusy
    
    @final
    def Dispose(self) -> None:
        self.__Reset()

class IEnum(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEnumValue(self) -> Enum:
        pass

def AsEnumValue(item: IEnum|Enum) -> Enum:
    return item.GetEnumValue() if isinstance(item, IEnum) else item

def AsUnderlyingEnumValue(item: IEnum|Enum) -> object:
    return AsEnumValue(item).value
def TryAsUnderlyingEnumValue(item: IEnum|Enum) -> int|None:
    value: object = AsUnderlyingEnumValue(item)

    return value if isinstance(value, int) else None

def AreEnumsEqual(x: IEnum|Enum, y: IEnum|Enum) -> bool:
    return AsEnumValue(x) == AsEnumValue(y)
def TryAreEnumsEqual(x: IEnum|Enum|None, y: IEnum|Enum|None) -> bool:
    return False if x is None or y is None else AreEnumsEqual(x, y)

def CompareEnums(x: IEnum|Enum, y: IEnum|Enum) -> INullable[bool|None]:
    def compare(x: int|None, y: int|None) -> INullable[bool|None]:
        def compare(x: int, y: int) -> bool|None:
            return None if x == y else y > x

        return (GetNullValue() if y is None else GetNullable(True)) if x is None else GetNullable(False if y is None else compare(x, y))
    
    return compare(TryAsUnderlyingEnumValue(x), TryAsUnderlyingEnumValue(y))
def TryCompare(x: IEnum|Enum|None, y: IEnum|Enum|None) -> INullable[bool|None]:
    return GetNullable(y is None) if x is None else (GetNullable(False) if y is None else CompareEnums(x, y))