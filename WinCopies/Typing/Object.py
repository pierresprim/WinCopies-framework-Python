from abc import abstractmethod
from enum import Enum
from typing import final, Type as TypeBase

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Enum import TryGetFieldFromValue
from WinCopies.Math import CompareTo
from WinCopies.Typing import IDisposable, IEquatableObject as IEquatableObjectBase, IEquatableItem, IComparableObject as IComparableObjectBase
from WinCopies.Typing.Reflection import IsOf

class IEquatableObject[T](IEquatableObjectBase[T], IEquatableItem):
    def __init__(self) -> None:
        super().__init__()

class IItem(IEquatableItem, IStringable):
    def __init__(self) -> None:
        super().__init__()

class IObject[T](IEquatableObject[T], IItem):
    def __init__(self) -> None:
        super().__init__()
class Object[T](Abstract, IObject[T]):
    def __init__(self) -> None:
        super().__init__()

class IComparableObject[T](IEquatableObject[T], IComparableObjectBase[T]):
    def __init__(self) -> None:
        super().__init__()
class IComparableItem[T: IEquatableItem](IObject[T], IComparableObject[T]):
    def __init__(self) -> None:
        super().__init__()

class IValueProvider(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetUnderlyingValue(self) -> object:
        pass
class IValueItem(IItem, IValueProvider):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> object:
        pass

class IComplexValueProvider[T](IValueProvider):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetUnderlyingValue(self) -> T:
        pass

class IComparableValue[T](IComparableObject[T], IValueItem):
    def __init__(self) -> None:
        super().__init__()
class IValueObject[TValue, TObject](IObject[TObject], IValueItem):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> TValue:
        pass
class IComplexValueObject[TValue, TUnderlying, TObject](IValueObject[TValue, TObject], IComplexValueProvider[TUnderlying]):
    def __init__(self) -> None:
        super().__init__()

class IComparableValueObject[TValue, TObject](IValueObject[TValue, TObject], IComparableValue[TObject]):
    def __init__(self) -> None:
        super().__init__()
class IComparableComplexValueObject[TValue, TUnderlying, TObject](IComplexValueObject[TValue, TUnderlying, TObject], IComparableValueObject[TValue, TObject]):
    def __init__(self) -> None:
        super().__init__()

class ValueObjectBase[TValue, TUnderlying, TObject](Object[TObject], IValueObject[TValue, TObject]):
    def __init__(self, value: TValue) -> None:
        super().__init__()

        self.__value: TValue = value
    
    @final
    def GetValue(self) -> TValue:
        return self.__value
    
    @abstractmethod
    def GetUnderlyingValue(self) -> TUnderlying:
        pass
class ValueObject[TValue, TObject](ValueObjectBase[TValue, TValue, TObject]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)
    
    @final
    def GetUnderlyingValue(self) -> TValue:
        return self.GetValue()

class IBoolean(IComparableValueObject[bool, 'IBoolean|bool']):
    def __init__(self) -> None:
        super().__init__()
class __Boolean(Abstract, IBoolean):
    def __init__(self) -> None:
        super().__init__()
    
    def GetUnderlyingValue(self) -> bool:
        return self.GetValue()
    
    def Equals(self, item: IBoolean|bool|object) -> bool:
        def equals(item: bool) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IBoolean) and equals(item.GetValue())) or (isinstance(item, bool) and equals(item))
    
    def CompareTo(self, item: IBoolean|bool|object) -> bool|None:
        def compareTo(item: bool) -> bool|None:
            return CompareTo(self.GetValue(), item)
        
        return (isinstance(item, IBoolean) and compareTo(item.GetValue())) or (isinstance(item, bool) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())

@final
class __True(__Boolean):
    def __init__(self) -> None:
        super().__init__()
    
    def GetValue(self) -> bool:
        return True
@final
class __False(__Boolean):
    def __init__(self) -> None:
        super().__init__()
    
    def GetValue(self) -> bool:
        return False

__true: IBoolean = __True()
__false: IBoolean = __False()

def GetTrueObject() -> IBoolean:
    return __true
def GetFalseObject() -> IBoolean:
    return __false

class IInteger(IComparableValueObject[int, 'IInteger|int']):
    def __init__(self) -> None:
        super().__init__()
class Integer(ValueObject[int, IInteger|int], IInteger):
    def __init__(self, value: int) -> None:
        super().__init__(value)
    
    @staticmethod
    def FromEnum(value: Enum) -> IInteger:
        return Integer(value.value)
    
    def Equals(self, item: IInteger|int|object) -> bool:
        def equals(item: int) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IInteger) and equals(item.GetValue())) or (isinstance(item, int) and equals(item))
    
    def CompareTo(self, item: IInteger|int|object) -> bool|None:
        def compareTo(item: int) -> bool|None:
            return CompareTo(self.GetValue(), item)
        
        return (isinstance(item, IInteger) and compareTo(item.GetValue())) or (isinstance(item, int) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())

class IEnum(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetEnumValue(self) -> Enum:
        pass
class IEnumValue[T: Enum](IComparableComplexValueObject[T, int, IEnum|Enum], IEnum):
    def __init__(self) -> None:
        super().__init__()
class EnumValue[T: Enum](ValueObjectBase[T, int, IEnum|Enum], IEnumValue[T]):
    def __init__(self, value: T) -> None:
        super().__init__(value)
    
    @final
    def GetEnumValue(self) -> Enum:
        return self.GetValue()
    @final
    def GetUnderlyingValue(self) -> int:
        return int(self.GetValue().value)
    
    @final
    def IsSameAs(self, value: Enum) -> bool:
        return IsOf(self.GetValue(), type(value))
    
    def Equals(self, item: IEnum|object) -> bool:
        def equals(item: Enum) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IEnum) and equals(item.GetEnumValue())) or (isinstance(item, Enum) and equals(item))
    
    def CompareTo(self, item: IEnumValue[T]|object) -> bool|None:
        def compareTo(item: Enum) -> bool|None:
            return self.IsSameAs(item) and CompareTo(self.GetUnderlyingValue(), item.value)
        
        return (isinstance(item, IEnum) and compareTo(item.GetEnumValue())) or (isinstance(item, Enum) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue().value)
    
    def ToString(self) -> str:
        return str(self.GetValue().name)

def CreateEnum[T: Enum](value: T) -> IEnumValue[T]:
    return EnumValue[T](value)
def TryCreateEnum[T: Enum](e: TypeBase[T], v: int) -> IEnumValue[T]|None:
    result: T|None = TryGetFieldFromValue(e, v)

    return None if result is None else CreateEnum(result)

class IString(IComparableValueObject[str, 'IString']):
    def __init__(self) -> None:
        super().__init__()
class String(ValueObject[str, IString], IString):
    def __init__(self, value: str) -> None:
        super().__init__(value)
    
    def Equals(self, item: IString|object) -> bool:
        def equals(item: str) -> bool:
            return String.AreEqual(self.GetValue(), item)
        
        return (isinstance(item, IString) and equals(item.GetValue())) or (isinstance(item, str) and equals(item))
    
    def CompareTo(self, item: IString|object) -> bool|None:
        def compareTo(item: str) -> bool|None:
            return String.Compare(self.GetValue(), item)
        
        return (isinstance(item, IString) and compareTo(item.GetValue())) or (isinstance(item, str) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return self.GetValue()
    
    @staticmethod
    def AsValue(item: IString|str) -> str:
        return item.GetValue() if isinstance(item, IString) else item
    
    @staticmethod
    def AreEqual(x: IString|str, y: IString|str) -> bool:
        return String.AsValue(x) == String.AsValue(y)
    @staticmethod
    def TryAreEqual(x: IString|str|None, y: IString|str|None) -> bool:
        return False if x is None or y is None else String.AreEqual(x, y)
    
    @staticmethod
    def Compare(x: IString|str, y: IString|str) -> bool|None:
        return None if x == y else y > x
    @staticmethod
    def TryCompare(x: IString|str|None, y: IString|str|None) -> bool|None:
        return False if x is None or y is None else String.Compare(x, y)

class IType[T](IValueObject[type[T], 'IType[T]']):
    def __init__(self) -> None:
        super().__init__()
class Type[T](ValueObject[type[T], IType[T]], IType[T]):
    def __init__(self, t: type[T]) -> None:
        super().__init__(t)
    
    def Equals(self, item: IType[T]|object) -> bool:
        def equals(item: type[T]) -> bool:
            return self.GetValue() == item
        
        return (isinstance(item, IType) and equals(item.GetValue())) or (isinstance(item, type) and equals(item)) # pyright: ignore[reportUnknownArgumentType]
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())
    
    @staticmethod
    def Create(value: T) -> IType[T]:
        return Type[T](type(value))

class IReference[T](IValueObject[T, 'IReference[T]']):
    def __init__(self) -> None:
        super().__init__()
class Reference[T](ValueObject[T, IReference[T]], IReference[T]):
    def __init__(self, parameter: T) -> None:
        super().__init__(parameter)
    
    def Equals(self, item: IReference[T]|object) -> bool:
        return self.GetValue() is item
    
    def Hash(self) -> int:
        return hash(self.GetValue())

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self) -> None:
        super().__init__()