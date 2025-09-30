from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from typing import final, Callable, Type as SystemType

import WinCopies

from WinCopies import IInterface, IStringable, Abstract

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
class Object[T](Abstract, IObject[T]):
    def __init__(self):
        super().__init__()

class IValueObject[TValue, TObject](IObject[TObject]):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> TValue:
        pass
class ValueObject[TValue, TObject](Object[TObject], IValueObject[TValue, TObject]):
    def __init__(self, value: TValue):
        super().__init__()

        self.__value: TValue = value
    
    @final
    def GetValue(self) -> TValue:
        return self.__value

class IInteger(IValueObject[int, 'IInteger']):
    def __init__(self):
        super().__init__()
class Integer(ValueObject[int, IInteger], IInteger):
    def __init__(self, value: int):
        super().__init__(value)
    
    @staticmethod
    def FromEnum(value: Enum) -> IInteger:
        return Integer(value.value)
    
    def Equals(self, item: IInteger|object) -> bool:
        def equals(item: int) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IInteger) and equals(item.GetValue())) or (isinstance(item, int) and equals(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())

class IEnumValue[T: Enum](IValueObject[T, 'IEnumValue']):
    def __init__(self):
        super().__init__()
class EnumValue[T: Enum](ValueObject[T, IEnumValue[T]], IEnumValue[T]):
    def __init__(self, value: T):
        super().__init__(value)
    
    def Equals(self, item: IEnumValue[T]|object) -> bool:
        def equals(item: Enum) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IEnumValue) and equals(item.GetValue())) or (isinstance(item, Enum) and equals(item)) # type: ignore
    
    def Hash(self) -> int:
        return hash(self.GetValue().value)
    
    def ToString(self) -> str:
        return str(self.GetValue().name)

class IString(IValueObject[str, 'IString']):
    def __init__(self):
        super().__init__()
class String(ValueObject[str, IString], IString):
    def __init__(self, value: str):
        super().__init__(value)
    
    def Equals(self, item: IString|object) -> bool:
        def equals(item: str) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IString) and equals(item.GetValue())) or (isinstance(item, str) and equals(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return self.GetValue()

class IType[T](IValueObject[type[T], 'IType']):
    def __init__(self):
        super().__init__()
class Type[T](ValueObject[type[T], IType[T]], IType[T]):
    def __init__(self, t: type[T]):
        super().__init__(t)
    
    def Equals(self, item: IType[T]|object) -> bool:
        def equals(item: type[T]) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IType) and equals(item.GetValue())) or (isinstance(item, type) and equals(item)) # type: ignore
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())
    
    @staticmethod
    def Create(value: T) -> IType[T]:
        return Type[T](type(value))

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
@final
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

def TryGetValueAs[TValue, TDefault](type: SystemType[TValue], value: object, default: TDefault) -> TValue|TDefault:
    return value if isinstance(value, type) else default
def TryGetAs[T](type: SystemType[T], value: object) -> T|None:
    return TryGetValueAs(type, value, None)