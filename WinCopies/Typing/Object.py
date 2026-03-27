from abc import abstractmethod
from decimal import Decimal as decimal
from enum import Enum
from typing import final, Type as TypeBase

from WinCopies import IInterface, IStringable, Abstract
from WinCopies.Enum import TryGetFieldFromValue
from WinCopies.Math import NumericalValue, CompareTo
from WinCopies.Typing import IDisposable, INullable, IEnum, IEquatableObject as IEquatableObjectBase, IEquatableItem, IComparableObject as IComparableObjectBase, AreEnumsEqual as _AreEnumsEqual, TryAreEnumsEqual as _TryAreEnumsEqual, CompareEnums as _CompareEnums, TryCompare as _TryCompare
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

class ValueObjectAbstract[TValue, TUnderlying, TObject](Object[TObject], IValueObject[TValue, TObject]):
    def __init__(self, value: TValue) -> None:
        super().__init__()

        self.__value: TValue = value
    
    @final
    def GetValue(self) -> TValue:
        return self.__value
    
    @abstractmethod
    def GetUnderlyingValue(self) -> TUnderlying:
        pass
class ValueObjectBase[TValue, TInterface](ValueObjectAbstract[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)
    
    @final
    def GetUnderlyingValue(self) -> TValue:
        return self.GetValue()
class ExtendedValueObjectBase[TValue, TObject, TInterface: IValueItem](ValueObjectBase[TValue, TObject|TInterface]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)
    
    @staticmethod
    @abstractmethod
    def _AreValuesEqual(x: TObject, y: TObject) -> bool:
        pass
    
    @staticmethod
    @abstractmethod
    def AsValue(item: TValue|TObject|TInterface) -> TObject:
        pass
    
    @staticmethod
    @final
    def AreEqual(x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool:
        return ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(x) == ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(y)
    @staticmethod
    @final
    def TryAreEqual(x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool:
        return False if x is None or y is None else ExtendedValueObjectBase[TValue, TObject, TInterface].AreEqual(x, y)
class ComparableValueObjectBase[TValue, TObject, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TObject, TInterface]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)
    
    @staticmethod
    @abstractmethod
    def _CompareTo(x: TObject, y: TObject) -> bool:
        pass
    
    @staticmethod
    @final
    def Compare(x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool|None:
        def compare(x: TObject, y: TObject) -> bool|None:
            return None if ComparableValueObjectBase[TValue, TObject, TInterface]._AreValuesEqual(x, y) else ComparableValueObjectBase[TValue, TObject, TInterface]._CompareTo(y, x)

        return compare(ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(x), ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(y))
    @staticmethod
    @final
    def TryCompare(x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool|None:
        return y is None if x is None else (False if y is None else ComparableValueObjectBase[TValue, TObject, TInterface].Compare(x, y))

class ValueObject[TValue, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)
class ComparableValueObject[TValue, TInterface: IValueItem](ComparableValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None:
        super().__init__(value)

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

type NumericalObject = IInteger|IFloat|IDecimal
type Numerical = NumericalValue|NumericalObject

class INumericalItem(IValueItem):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def GetValue(self) -> NumericalValue:
        pass
class INumericalValue[T: NumericalValue](IComparableValueObject[T, Numerical], INumericalItem):
    def __init__(self) -> None:
        super().__init__()

class IInteger(INumericalValue[int]):
    def __init__(self) -> None:
        super().__init__()
class IFloat(INumericalValue[float]):
    def __init__(self) -> None:
        super().__init__()
class IDecimal(INumericalValue[decimal]):
    def __init__(self) -> None:
        super().__init__()

def TryMapNumericalValue(obj: object) -> NumericalValue|None:
    match obj:
        case int() | float() | decimal():
            return obj
        
        case _:
            return None
def TryMapNumerical(obj: IValueItem) -> INumericalItem|None:
    return obj if isinstance(obj, INumericalItem) else None

def UnderlyingValueEquals(x: NumericalValue, y: object) -> bool:
    value: NumericalValue|None = TryMapNumericalValue(y)

    return value is not None and x == value
def ValueEquals(x: INumericalItem, y: object) -> bool:
    return UnderlyingValueEquals(x.GetValue(), y)

def Equals(x: INumericalItem, y: INumericalItem) -> bool:
    value: INumericalItem|None = TryMapNumerical(y)

    return value is not None and x.GetValue() == value.GetValue()

def CompareUnderlyingValue(x: NumericalValue, y: object) -> bool|None:
    value: NumericalValue|None = TryMapNumericalValue(y)

    return value is not None and CompareTo(x, value)
def CompareValue(x: INumericalItem, y: object) -> bool|None:
    return CompareUnderlyingValue(x.GetValue(), y)

def Compare(x: INumericalItem, y: INumericalItem) -> bool|None:
    value: INumericalItem|None = TryMapNumerical(y)

    return value is not None and CompareTo(x.GetValue(), value.GetValue())

class _NumericalValue[T: NumericalValue](ComparableValueObjectBase[T, NumericalValue, NumericalObject], INumericalValue[T]):
    def __init__(self, value: T) -> None:
        super().__init__(value)
    
    def Equals(self, item: Numerical|object) -> bool:
        return Equals(self, item) if isinstance(item, INumericalItem) else ValueEquals(self, item)
    
    def CompareTo(self, item: Numerical|object) -> bool|None:
        def compareTo(item: int) -> bool|None:
            return CompareTo(self.GetValue(), item)
        
        return (isinstance(item, IInteger) and compareTo(item.GetValue())) or (isinstance(item, int) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return str(self.GetValue())
    
    @staticmethod
    @final
    def _AreValuesEqual(x: NumericalValue, y: NumericalValue) -> bool:
        return x == y
    @staticmethod
    @final
    def _CompareTo(x: NumericalValue, y: NumericalValue) -> bool:
        return x > y
    
    @staticmethod
    @final
    def AsValue(item: T|Numerical) -> NumericalValue:
        return item.GetValue() if isinstance(item, (IInteger, IFloat, IDecimal)) else item

class Integer(_NumericalValue[int], IInteger):
    def __init__(self, value: int) -> None:
        super().__init__(value)
    
    @staticmethod
    def FromEnum(value: Enum) -> IInteger:
        return Integer(value.value)
class Float(_NumericalValue[float], IFloat):
    def __init__(self, value: float) -> None:
        super().__init__(value)
class Decimal(_NumericalValue[decimal], IDecimal):
    def __init__(self, value: decimal) -> None:
        super().__init__(value)

class IEnumValue[T: Enum](IComparableComplexValueObject[T, int, IEnum|Enum], IEnum):
    def __init__(self) -> None:
        super().__init__()
class EnumValue[T: Enum](ValueObjectAbstract[T, int, IEnum|Enum], IEnumValue[T]):
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

def AreEnumsEqual[T: IEnum|Enum](x: T, y: T) -> bool:
    return _AreEnumsEqual(x, y)
def TryAreEnumsEqual[T: IEnum|Enum](x: T|None, y: T|None) -> bool:
    return _TryAreEnumsEqual(x, y)

def CompareEnums[T: IEnum|Enum](x: T, y: T) -> INullable[bool|None]:
    return _CompareEnums(x, y)
def TryCompare[T: IEnum|Enum](x: T|None, y: T|None) -> INullable[bool|None]:
    return _TryCompare(x, y)

def CreateEnum[T: Enum](value: T) -> IEnumValue[T]:
    return EnumValue[T](value)
def TryCreateEnum[T: Enum](e: TypeBase[T], v: int) -> IEnumValue[T]|None:
    result: T|None = TryGetFieldFromValue(e, v)

    return None if result is None else CreateEnum(result)

class IString(IComparableValueObject[str, 'IString']):
    def __init__(self) -> None:
        super().__init__()
class String(ComparableValueObject[str, IString], IString):
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
    @final
    def _AreValuesEqual(x: str, y: str) -> bool:
        return x == y
    @staticmethod
    @final
    def _CompareTo(x: str, y: str) -> bool:
        return x > y
    
    @staticmethod
    @final
    def AsValue(item: str|IString) -> str:
        return item.GetValue() if isinstance(item, IString) else item

class IByteArray(IValueObject[bytes, 'IByteArray']):
    def __init__(self) -> None:
        super().__init__()
class ByteArray(ComparableValueObject[bytes, IByteArray], IByteArray):
    def __init__(self, value: bytes) -> None:
        super().__init__(value)
    
    def Equals(self, item: IByteArray|object) -> bool:
        def equals(item: bytes) -> bool:
            return ByteArray.AreEqual(self.GetValue(), item)
        
        return (isinstance(item, IByteArray) and equals(item.GetValue())) or (isinstance(item, bytes) and equals(item))
    
    def CompareTo(self, item: IByteArray|object) -> bool|None:
        def compareTo(item: bytes) -> bool|None:
            return ByteArray.Compare(self.GetValue(), item)
        
        return (isinstance(item, IByteArray) and compareTo(item.GetValue())) or (isinstance(item, bytes) and compareTo(item))
    
    def Hash(self) -> int:
        return hash(self.GetValue())
    
    def ToString(self) -> str:
        return super(IInterface, self).__str__()
    
    @staticmethod
    @final
    def _AreValuesEqual(x: bytes, y: bytes) -> bool:
        return x == y
    @staticmethod
    @final
    def _CompareTo(x: bytes, y: bytes) -> bool:
        return x > y
    
    @staticmethod
    @final
    def AsValue(item: bytes|IByteArray) -> bytes:
        return item.GetValue() if isinstance(item, IByteArray) else item

class IType[T](IValueObject[type[T], 'IType[T]']):
    def __init__(self) -> None:
        super().__init__()
class Type[T](ValueObjectBase[type[T], IType[T]], IType[T]):
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
class Reference[T](ValueObjectBase[T, IReference[T]], IReference[T]):
    def __init__(self, parameter: T) -> None:
        super().__init__(parameter)
    
    def Equals(self, item: IReference[T]|object) -> bool:
        return self.GetValue() is item
    
    def Hash(self) -> int:
        return hash(self.GetValue())

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self) -> None:
        super().__init__()