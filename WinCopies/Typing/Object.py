from abc import abstractmethod
from enum import Enum
from typing import final

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Typing import IDisposable, IEquatable, IEquatableItem
from WinCopies.Typing.Reflection import EnsureDirectModuleCall

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

class IValueProvider(IInterface):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetUnderlyingValue(self) -> object:
        pass
class IValueItem(IItem, IValueProvider):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> object:
        pass
class IValueObject[TValue, TObject](IObject[TObject], IValueItem):
    def __init__(self):
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> TValue:
        pass
class ValueObjectBase[TValue, TUnderlying, TObject](Object[TObject], IValueObject[TValue, TObject]):
    def __init__(self, value: TValue):
        super().__init__()

        self.__value: TValue = value
    
    @final
    def GetValue(self) -> TValue:
        return self.__value
    
    @abstractmethod
    def GetUnderlyingValue(self) -> TUnderlying:
        pass
class ValueObject[TValue, TObject](ValueObjectBase[TValue, TValue, TObject]):
    def __init__(self, value: TValue):
        super().__init__(value)
    
    @final
    def GetUnderlyingValue(self) -> TValue:
        return self.GetValue()

class IBoolean(IValueObject[bool, 'IBoolean']):
    def __init__(self):
        super().__init__()
class __Boolean(Abstract, IBoolean):
    def __init__(self):
        EnsureDirectModuleCall()

        super().__init__()
    
    def GetUnderlyingValue(self) -> bool:
        return self.GetValue()
    
    def Equals(self, item: IBoolean|object) -> bool:
        def equals(item: int) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IBoolean) and equals(item.GetValue())) or (isinstance(item, bool) and equals(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())

@final
class __True(__Boolean):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> bool:
        return True
@final
class __False(__Boolean):
    def __init__(self):
        super().__init__()
    
    def GetValue(self) -> bool:
        return True

__true: IBoolean = __True()
__false: IBoolean = __False()

def GetTrueObject() -> IBoolean:
    return __true
def GetFalseObject() -> IBoolean:
    return __false

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
class EnumValue[T: Enum](ValueObjectBase[T, int, IEnumValue[T]], IEnumValue[T]):
    def __init__(self, value: T):
        super().__init__(value)
    
    @final
    def GetUnderlyingValue(self) -> int:
        return self.GetValue().value
    
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

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self):
        super().__init__()