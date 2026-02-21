from __future__ import annotations

from abc import abstractmethod
from typing import final, Type as SystemType

from WinCopies import IInterface, IDisposable as IDisposableBase, Abstract
from WinCopies.Typing.Delegate import Converter

class IStruct[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        pass
    @abstractmethod
    def SetValue(self, value: T) -> None:
        pass
class Struct[T](Abstract, IStruct[T]):
    def __init__(self, value: T) -> None:
        super().__init__()

        self.__value: T = value
    
    @final
    def GetValue(self) -> T:
        return self.__value
    def SetValue(self, value: T) -> None:
        self.__value = value

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

class IComparable[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CompareTo(self, item: T) -> bool|None:
        pass

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
class __Nullable[T](Abstract, INullable[T]):
    def __init__(self, value: T) -> None:
        super().__init__()
        
        self.__value: T = value
    
    def HasValue(self) -> bool:
        return True
    def GetValue(self) -> T:
        return self.__value
@final
class __NullValue[T](Abstract, INullable[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def HasValue(self) -> bool:
        return False
    def GetValue(self) -> T:
        raise InvalidOperationError()

__nullValue: __NullValue = __NullValue() # type: ignore

def GetNullable[T](value: T) -> INullable[T]:
    return __Nullable[T](value)
def GetNullValue[T]() -> INullable[T]: # pyright: ignore[reportInvalidTypeVarUse]
    return __nullValue # pyright: ignore[reportUnknownVariableType]

def TryGetValue[T](value: INullable[T]|None) -> T|None:
    return None if value is None else value.TryGetValue()

class __IDisposableProviderItem[T: IDisposableInfo](IInterface):
    def __init__(self) -> None:
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
class __DisposedItem[T: IDisposableInfo](Abstract, __IDisposableProviderItem[T]):
    def __init__(self) -> None:
        super().__init__()
    
    def GetItem(self) -> T:
        raise GetDisposedError()

    def IsDisposed(self) -> bool:
        return True

    def Dispose(self) -> __IDisposableProviderItem[T]:
        return self

__disposedItem = __DisposedItem() # type: ignore

@final
class __DisposableProviderItem[T: IDisposableInfo](Abstract, __IDisposableProviderItem[T]):
    def __init__(self, item: T) -> None:
        super().__init__()

        self.__item: T = item
    
    def GetItem(self) -> T:
        return self.__item

    def IsDisposed(self) -> bool:
        return self.__item.IsDisposed()
    
    def Dispose(self) -> __IDisposableProviderItem[T]:
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