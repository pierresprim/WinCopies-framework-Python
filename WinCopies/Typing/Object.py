from __future__ import annotations

from abc import abstractmethod
from datetime import date, time, datetime, timedelta
from decimal import Decimal as decimal
from enum import Enum
from typing import final, Any, Type as TypeBase
from weakref import finalize, ref, ReferenceType

from WinCopies import IInterface, IDisposableBase, IStringable, Abstract
from WinCopies.Collections.Generation import IRemovable
from WinCopies.Delegates import NoAction, FuncNone
from WinCopies.Enum import TryGetFieldFromValue, AreEnumsEqual as _AreEnumsEqual, TryAreEnumsEqual as _TryAreEnumsEqual, CompareEnums as _CompareEnums, TryCompare as _TryCompare
from WinCopies.Typing import NumericalValue, INullable, IDisposable, IEnumBase, IEnum
from WinCopies.Typing.Comparison import IEquatableBase, IHashableBase, IHashableItem, IHashableComparableItem, Equals as _Equals, CompareTo
from WinCopies.Typing.Delegate import Action, NullableFunction, ItemComparison
from WinCopies.Typing.Enum import IntEnum, IntegerEnum, StringEnum, EquatableEnumProtocol, ComparableEnumProtocol
from WinCopies.Typing.Protocols import SupportsStringization, EquatableObject as EquatableObjectProtocol, ComparableObject as ComparableObjectProtocol
from WinCopies.Typing.Reflection import IsOf, GetType, GetTypeName

class IItem(IHashableBase, IEquatableBase, IStringable):
    def __init__(self) -> None: super().__init__()

class IObject[T](IHashableItem[T|object], IItem):
    def __init__(self) -> None: super().__init__()
class Object[T](Abstract, IObject[T]):
    def __init__(self) -> None: super().__init__()

class IComparableItem[T](IHashableComparableItem[T], IItem):
    def __init__(self) -> None: super().__init__()
class IComparableObject[T](IObject[T], IHashableComparableItem[T]):
    def __init__(self) -> None: super().__init__()

class IValueProvider(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetUnderlyingValue(self) -> object:
        ...
class IValueItem(IItem, IValueProvider):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValue(self) -> object:
        ...

class IComplexValueProvider[T](IValueProvider):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetUnderlyingValue(self) -> T:
        ...

class IComparable[T](IComparableObject[T], IValueItem):
    def __init__(self) -> None: super().__init__()
class IValueObject[T](IValueItem):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValue(self) -> T:
        ...

class IItemObject[TValue, TObject](IObject[TValue|TObject], IValueObject[TValue]):
    def __init__(self) -> None: super().__init__()
class IComplexValueObject[TValue, TUnderlying, TObject](IItemObject[TValue, TObject], IComplexValueProvider[TUnderlying]):
    def __init__(self) -> None: super().__init__()

class IComparableValueObject[TValue, TObject](IItemObject[TValue, TObject], IComparable[TValue|TObject]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsComparableValue(self) -> TValue: return self.GetValue()

class IEquatableComplexValueObject[TValue, TUnderlying, TObject](IComplexValueObject[TValue, TUnderlying, TObject], IItemObject[TValue, TObject]):
    def __init__(self) -> None: super().__init__()
class IComparableComplexValueObject[TValue, TUnderlying, TObject](IEquatableComplexValueObject[TValue, TUnderlying, TObject], IComparableValueObject[TValue, TObject]):
    def __init__(self) -> None: super().__init__()

class ValueObjectAbstract[TValue, TUnderlying, TObject](Object[TValue|TUnderlying|TObject], IItemObject[TValue, TObject]):
    def __init__(self, value: TValue) -> None:
        super().__init__()

        self.__value: TValue = value
    
    @final
    def GetValue(self) -> TValue: return self.__value
    
    @abstractmethod
    def GetUnderlyingValue(self) -> TUnderlying:
        ...
class ValueObjectBase[TValue, TInterface](ValueObjectAbstract[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
    
    @final
    def GetUnderlyingValue(self) -> TValue: return self.GetValue()
class ExtendedValueObjectBase[TValue, TObject, TInterface: IValueItem](ValueObjectBase[TValue, TObject|TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
    
    @classmethod
    @abstractmethod
    def AsValue(cls, item: TValue|TObject|TInterface) -> TObject:
        ...
    
    @classmethod
    @final
    def AreEqual(cls, x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool:
        return cls.AsValue(x) == cls.AsValue(y)
    @classmethod
    @final
    def TryAreEqual(cls, x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool:
        return False if x is None or y is None else ExtendedValueObjectBase[TValue, TObject, TInterface].AreEqual(x, y)
class ComparableValueObjectBase[TValue: SupportsStringization, TObject, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TObject, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
    
    @classmethod
    @abstractmethod
    def _AreValuesEqual(cls, x: TObject, y: TObject) -> bool:
        ...
    
    @classmethod
    @abstractmethod
    def _CompareValues(cls, x: TObject, y: TObject) -> bool:
        ...
    
    @classmethod
    @final
    def Compare(cls, x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool|None:
        def compare(x: TObject, y: TObject) -> bool|None: return None if cls._AreValuesEqual(x, y) else cls._CompareValues(y, x)

        return compare(cls.AsValue(x), cls.AsValue(y))
    @classmethod
    @final
    def TryCompare(cls, x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool|None:
        return y is None if x is None else (False if y is None else cls.Compare(x, y))

class ValueObject[TValue, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
class ComparableValueObject[TValue, TInterface: IValueItem](ComparableValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)

class IEquatableValueItemAbstract[TInterface, TValue](IItemObject[TValue, TInterface]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def GetValueType(self) -> TypeBase[TValue]:
        ...
class IEquatableValueItemBase[TObject, TInterface, TValue](IEquatableValueItemAbstract[TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @abstractmethod
    def GetObjectType(cls) -> TypeBase[TObject]:
        ...
class IEquatableValueItem[TObject, TValue](IEquatableValueItemBase[TObject, TObject, TValue]):
    def __init__(self) -> None: super().__init__()

class IComparableValueItemBase[TObject, TInterface, TValue](IEquatableValueItemBase[TObject, TInterface, TValue], IComparableValueObject[TValue, TInterface]):
    def __init__(self) -> None: super().__init__()
class IComparableValueItem[TObject, TValue](IComparableValueItemBase[TObject, TObject, TValue], IEquatableValueItem[TObject, TValue]):
    def __init__(self) -> None: super().__init__()

class IHashableValueBase[TObject, TInterface, TValue](IEquatableValueItemBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

    def Hash(self) -> int: return hash(self.GetValue())
class IHashableValue[TObject, TValue](IHashableValueBase[TObject, TObject, TValue]):
    def __init__(self) -> None: super().__init__()

class IStringableValueBase[TObject, TInterface, TValue](IEquatableValueItemBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()
    
    def ToString(self) -> str: return str(self.GetValue())
class IStringableValue[TObject, TValue](IStringableValueBase[TObject, TObject, TValue]):
    def __init__(self) -> None: super().__init__()



class EquatableValueAbstract[TObject: IValueItem, TInterface, TValue](IEquatableValueItemBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @abstractmethod
    def _GetItemAsObject(cls, item: TObject) -> IItemObject[TValue, TInterface]:
        ...
    
    def _CompareValueTo[TResult](self, item: TObject|TValue|object, predicate: ItemComparison[TValue, TResult]) -> bool|TResult:
        def compare(item: TValue) -> TResult: return predicate(self.GetValue(), item)

        return (isinstance(item, self.GetObjectType()) and compare(self._GetItemAsObject(item).GetValue())) or (isinstance(item, self.GetValueType()) and compare(item))
class EquatableValueBase[TObject: IValueItem, TInterface, TValue: EquatableObjectProtocol](EquatableValueAbstract[TObject, TInterface, TValue], IHashableValueBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

    def Equals(self, item: TObject|TValue|object) -> bool: return self._CompareValueTo(item, _Equals)
class EquatableValue[TObject: IValueItem, TInterface, TValue: EquatableObjectProtocol](EquatableValueBase[TObject, TInterface, TValue], IStringableValueBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()



class EquatableValueItemAbstract[TObject: IValueItem, TValue](EquatableValueAbstract[TObject, TObject, TValue], IEquatableValueItem[TObject, TValue]):
    def __init__(self) -> None: super().__init__()
class EquatableValueItemBase[TObject: IValueItem, TValue: EquatableObjectProtocol](EquatableValueItemAbstract[TObject, TValue], EquatableValueBase[TObject, TObject, TValue], IHashableValue[TObject, TValue]):
    def __init__(self) -> None: super().__init__()
class EquatableValueItem[TObject: IValueItem, TValue: EquatableObjectProtocol](EquatableValueItemBase[TObject, TValue], EquatableValue[TObject, TObject, TValue], IStringableValue[TObject, TValue]):
    def __init__(self) -> None: super().__init__()



class EquatableValueObject[TObject: IValueItem, TValue: EquatableObjectProtocol](ValueObject[TValue, TObject], EquatableValueItem[TObject, TValue]):
    def __init__(self, value: TValue) -> None: super().__init__(value)



class ComparableValueBase[TObject: IValueItem, TInterface, TValue: ComparableObjectProtocol](EquatableValueBase[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @abstractmethod
    def _GetItemAsObject(cls, item: TObject) -> IComparableValueObject[TValue, TInterface]:
        ...
    
    def _CompareTo(self, item: TObject|TValue|object) -> bool|None: return self._CompareValueTo(item, CompareTo)
class ComparableValue[TObject: IValueItem, TInterface, TValue: ComparableObjectProtocol](ComparableValueBase[TObject, TInterface, TValue], EquatableValue[TObject, TInterface, TValue]):
    def __init__(self) -> None: super().__init__()

class ComparableValueItemBase[TObject: IValueItem, TValue: ComparableObjectProtocol](ComparableValueBase[TObject, TObject, TValue], EquatableValueItemBase[TObject, TValue], IComparableValueItem[TObject, TValue]):
    def __init__(self) -> None: super().__init__()
class ComparableValueItem[TObject: IValueItem, TValue: ComparableObjectProtocol](ComparableValueItemBase[TObject, TValue], ComparableValue[TObject, TObject, TValue], EquatableValueItem[TObject, TValue]):
    def __init__(self) -> None: super().__init__()

class Comparable[TObject: IValueItem, TValue: ComparableObjectProtocol](ComparableValueObject[TValue, TObject], ComparableValueItem[TObject, TValue]):
    def __init__(self, value: TValue) -> None: super().__init__(value)

class IBoolean(IComparableValueItem["IBoolean", bool]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IBoolean]: return IBoolean
    @final
    def GetValueType(self) -> TypeBase[bool]: return bool
class __Boolean(Abstract, ComparableValueItem[IBoolean, bool], IBoolean):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IBoolean) -> IComparableValueObject[bool, IBoolean]: return item
    
    def GetUnderlyingValue(self) -> bool: return self.GetValue()

@final
class __True(__Boolean):
    def __init__(self) -> None: super().__init__()
    
    def GetValue(self) -> bool: return True
@final
class __False(__Boolean):
    def __init__(self) -> None: super().__init__()
    
    def GetValue(self) -> bool: return False

__true: IBoolean = __True()
__false: IBoolean = __False()

def GetTrueObject() -> IBoolean: return __true
def GetFalseObject() -> IBoolean: return __false

class INumericalItem(IValueItem):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValue(self) -> NumericalValue:
        ...
class INumericalValue[T: NumericalValue](IComparableValueObject[T, "Numerical"], INumericalItem):
    def __init__(self) -> None: super().__init__()

class IInteger(INumericalValue[int]):
    def __init__(self) -> None: super().__init__()
class IFloat(INumericalValue[float]):
    def __init__(self) -> None: super().__init__()
class IDecimal(INumericalValue[decimal]):
    def __init__(self) -> None: super().__init__()

type NumericalObject = IInteger|IFloat|IDecimal
type Numerical = NumericalValue|NumericalObject

def TryMapNumericalValue(obj: object) -> NumericalValue|None:
    match obj:
        case int() | float() | decimal(): return obj
        
        case _: return None
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
    def __init__(self, value: T) -> None: super().__init__(value)
    
    def _CompareTo(self, item: Numerical|object) -> bool|None: return Compare(self, item) if isinstance(item, INumericalItem) else CompareValue(self, item)
    
    @classmethod
    @final
    def _AreValuesEqual(cls, x: NumericalValue, y: NumericalValue) -> bool:
        return x == y
    @classmethod
    @final
    def _CompareValues(cls, x: NumericalValue, y: NumericalValue) -> bool:
        return x > y
    
    @classmethod
    @final
    def AsValue(cls, item: T|Numerical) -> NumericalValue:
        return item.GetValue() if isinstance(item, (IInteger, IFloat, IDecimal)) else item
    
    def Equals(self, item: Numerical|object) -> bool: return Equals(self, item) if isinstance(item, INumericalItem) else ValueEquals(self, item)
    def Hash(self) -> int: return hash(self.GetValue())
    
    def ToString(self) -> str: return str(self.GetValue())

class Integer(_NumericalValue[int], IInteger):
    def __init__(self, value: int) -> None: super().__init__(value)
    
    @staticmethod
    def FromEnum(value: IntegerEnum) -> IInteger:
        return Integer(value.value)
class Float(_NumericalValue[float], IFloat):
    def __init__(self, value: float) -> None: super().__init__(value)
class Decimal(_NumericalValue[decimal], IDecimal):
    def __init__(self, value: decimal) -> None: super().__init__(value)

class IEnumValueBase[TEnum: EquatableEnumProtocol, TValue: EquatableObjectProtocol](IEquatableComplexValueObject[TEnum, TValue, IEnum[TEnum]|TEnum], IEnum[TEnum], IEquatableValueItemAbstract[IEnum[TEnum]|TEnum, TEnum]):
    def __init__(self) -> None: super().__init__()

    @final
    def GetValueType(self) -> TypeBase[TEnum]: return type(self.GetValue())
    
    @final
    def GetEnumValue(self) -> TEnum: return self.GetValue()
    
    @final
    def IsSameAs(self, value: Enum) -> bool:
        return IsOf(self.GetValue(), type(value))
    
    def Hash(self) -> int: return hash(self.GetValue().value)

class IEnumValue[TEnum: EquatableEnumProtocol, TValue: EquatableObjectProtocol](IEnumValueBase[TEnum, TValue], IEquatableValueItemBase["IEnumValue[TEnum, TValue]", IEnum[TEnum]|TEnum, TEnum]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IEnumValue[TEnum, TValue]]: return IEnumValue[TEnum, TValue]
class IComparableEnumValue[TEnum: ComparableEnumProtocol, TValue: ComparableObjectProtocol](IEnumValueBase[TEnum, TValue], IComparableComplexValueObject[TEnum, TValue, IEnum[TEnum]|TEnum], IEnum[TEnum], IComparableValueItemBase["IComparableEnumValue[TEnum, TValue]", IEnum[TEnum]|TEnum, TEnum]):
    def __init__(self) -> None: super().__init__()
    
    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IComparableEnumValue[TEnum, TValue]]: return IComparableEnumValue[TEnum, TValue]

class IIntegerEnumValue[T: IntegerEnum](IComparableEnumValue[T, int]):
    def __init__(self) -> None: super().__init__()
class IStringEnumValue[T: StringEnum](IEnumValue[T, str]):
    def __init__(self) -> None: super().__init__()

class _EnumValueBase[TObject: IValueItem, TEnum: EquatableEnumProtocol, TValue: EquatableObjectProtocol](ValueObjectAbstract[TEnum, TValue, IEnum[TEnum]|Enum], EquatableValue[TObject, IEnum[TEnum]|TEnum, TEnum]):
    def __init__(self, value: TEnum) -> None: super().__init__(value)

class EnumValue[TEnum: EquatableEnumProtocol, TValue: EquatableObjectProtocol](_EnumValueBase[IEnumValue[TEnum, TValue], TEnum, TValue], IEnumValue[TEnum, TValue]):
    def __init__(self, value: TEnum) -> None: super().__init__(value)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IEnumValue[TEnum, TValue]) -> IItemObject[TEnum, IEnum[TEnum]|TEnum]: return item
class ComparableEnumValue[TEnum: ComparableEnumProtocol, TValue: ComparableObjectProtocol](_EnumValueBase[IComparableEnumValue[TEnum, TValue], TEnum, TValue], ComparableValue[IComparableEnumValue[TEnum, TValue], IEnum[TEnum]|TEnum, TEnum], IComparableEnumValue[TEnum, TValue]):
    def __init__(self, value: TEnum) -> None: super().__init__(value)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IComparableEnumValue[TEnum, TValue]) -> IComparableValueObject[TEnum, IEnum[TEnum]|TEnum]: return item

class IntegerEnumValue[T: IntegerEnum](ComparableEnumValue[T, int], IIntegerEnumValue[T]):
    def __init__(self, value: T) -> None: super().__init__(value)

    @final
    def GetUnderlyingValue(self) -> int: return self.GetValue().value
class StringEnumValue[T: StringEnum](EnumValue[T, str], IStringEnumValue[T]):
    def __init__(self, value: T) -> None: super().__init__(value)

    @final
    def GetUnderlyingValue(self) -> str: return self.GetValue().value

def AreEnumsEqual[T: IEnumBase|Enum](x: T, y: T) -> bool:
    return _AreEnumsEqual(x, y)
def TryAreEnumsEqual[T: IEnumBase|Enum](x: T|None, y: T|None) -> bool:
    return _TryAreEnumsEqual(x, y)

def CompareEnums[T: IntegerEnum](x: IEnum[T]|T, y: IEnum[T]|T) -> bool|None:
    return _CompareEnums(x, y)
def TryCompare[T: IntegerEnum](x: IEnum[T]|T|None, y: IEnum[T]|T|None) -> INullable[bool|None]:
    return _TryCompare(x, y)

def CreateIntegerEnum[T: IntegerEnum](value: T) -> IComparableEnumValue[T, int]:
    return IntegerEnumValue[T](value)
def TryCreateIntegerEnum[T: IntegerEnum](e: TypeBase[T], v: int) -> IComparableEnumValue[T, int]|None:
    result: T|None = TryGetFieldFromValue(e, v)

    return None if result is None else CreateIntegerEnum(result)

def CreateStringEnum[T: StringEnum](value: T) -> IEnumValue[T, str]:
    return StringEnumValue[T](value)
def TryCreateStringEnum[T: StringEnum](e: TypeBase[T], v: str) -> IEnumValue[T, str]|None:
    result: T|None = TryGetFieldFromValue(e, v)

    return None if result is None else CreateStringEnum(result)

class IString(IComparableValueItem['IString', str]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IString]: return IString
    @final
    def GetValueType(self) -> TypeBase[str]: return str
class String(Comparable[IString, str], IString):
    def __init__(self, value: str) -> None: super().__init__(value)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IString) -> IComparableValueObject[str, IString]: return item
    
    @classmethod
    @final
    def _AreValuesEqual(cls, x: str, y: str) -> bool:
        return x == y
    @classmethod
    @final
    def _CompareValues(cls, x: str, y: str) -> bool:
        return x > y
    
    @classmethod
    @final
    def AsValue(cls, item: str|IString) -> str:
        return item.GetValue() if isinstance(item, IString) else item
    
    def ToString(self) -> str: return self.GetValue()

class IByteArray(IComparableValueItem['IByteArray', bytes]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IByteArray]: return IByteArray
    @final
    def GetValueType(self) -> TypeBase[bytes]: return bytes
class ByteArray(Comparable[IByteArray, bytes], IByteArray):
    def __init__(self, value: bytes) -> None: super().__init__(value)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IByteArray) -> IComparableValueObject[bytes, IByteArray]: return item
    
    @classmethod
    @final
    def _AreValuesEqual(cls, x: bytes, y: bytes) -> bool:
        return x == y
    @classmethod
    @final
    def _CompareValues(cls, x: bytes, y: bytes) -> bool:
        return x > y
    
    @classmethod
    @final
    def AsValue(cls, item: bytes|IByteArray) -> bytes:
        return item.GetValue() if isinstance(item, IByteArray) else item
    
    def ToString(self) -> str: return super(IInterface, self).__str__()

class IType[T](IEquatableValueItem['IType[T]', TypeBase[T]]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IType[T]]: return IType[T]
    @final
    def GetValueType(self) -> TypeBase[type]: return type
class Type[T](ValueObjectBase[TypeBase[T], IType[T]], IType[T], EquatableValueItemAbstract[IType[T], TypeBase[T]], IHashableValue[IType[T], TypeBase[T]]):
    def __init__(self, t: TypeBase[T]) -> None: super().__init__(t)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IType[T]) -> IItemObject[TypeBase[T], IType[T]]: return item
    
    def Equals(self, item: IType[T]|TypeBase[T]|object) -> bool: return self._CompareValueTo(item, lambda x, y: x == y)
    
    def ToString(self) -> str: return str(self.GetValue())

class IReference[T](IEquatableValueItem['IReference[T]', T]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @final
    def GetObjectType(cls) -> TypeBase[IReference[T]]: return IReference[T]

class Reference[T](ValueObjectBase[T, IReference[T]], EquatableValueItemAbstract[IReference[T], T], IReference[T]):
    def __init__(self, value: T) -> None: super().__init__(value)

    @classmethod
    @final
    def _GetItemAsObject(cls, item: IReference[T]) -> IItemObject[T, IReference[T]]: return item

    @final
    def GetValueType(self) -> TypeBase[T]: return type(self.GetValue())
    
    def Equals(self, item: IReference[T]|object) -> bool:
        def equals(item: Any) -> bool: return self.GetValue() is item
        
        return equals(item.GetValue()) if isinstance(item, IReference) else equals(item)
    def Hash(self) -> int: return hash(id(self.GetValue()))
class DefaultReference[T](Reference[T]):
    def __init__(self, value: T) -> None: super().__init__(value)
    
    def ToString(self) -> str: return super(IInterface, self).__str__()

def CreateType[T](value: T|TypeBase[T]) -> IType[T]:
    return Type[T](GetType(value))
def CreateReference[T](value: T) -> IReference[T]:
    return DefaultReference[T](value)

class IDate(IItemObject[date, "time|datetime|timedelta|DateTimeOrDeltaItem"], IComparable["date|IDate|ITime|IDateTime|ITimeDelta"]):
    def __init__(self) -> None: super().__init__()
class ITime(IItemObject[time, "date|datetime|timedelta|DateTimeOrDeltaItem"], IComparable["time|IDate|ITime|IDateTime|ITimeDelta"]):
    def __init__(self) -> None: super().__init__()
class IDateTime(IItemObject[datetime, "DateOrTimeValue|timedelta|DateTimeOrDeltaItem"], IComparable["datetime|IDate|ITime|IDateTime|ITimeDelta"]):
    def __init__(self) -> None: super().__init__()
class ITimeDelta(IItemObject[timedelta, "DateAndTimeValue|DateTimeOrDeltaItem"], IComparable["timedelta|IDate|ITime|IDateTime|ITimeDelta"]):
    def __init__(self) -> None: super().__init__()

type DateOrTimeValue = date|time
type DateAndTimeValue = DateOrTimeValue|datetime
type DateTimeOrDeltaValue = DateAndTimeValue|timedelta

type DateOrTimeItem = IDate|ITime
type DateAndTimeItem = DateOrTimeItem|IDateTime
type DateTimeOrDeltaItem = DateAndTimeItem|ITimeDelta

type DateOrTime = DateOrTimeValue|DateOrTimeItem
type DateAndTime = DateOrTime|DateAndTimeValue|DateAndTimeItem
type DateTimeOrDelta = DateAndTime|DateTimeOrDeltaValue|DateTimeOrDeltaItem

class _DateTime[TValue: DateTimeOrDeltaValue, TInterface: DateTimeOrDeltaItem](ExtendedValueObjectBase[TValue, DateTimeOrDeltaValue, DateTimeOrDeltaItem]):
    def __init__(self, value: TValue) -> None: super().__init__(value)

    @final
    def _AsComparableValue(self) -> TValue: return self.GetValue()
    
    def Equals(self, item: TValue|TInterface|object) -> bool:
        def equals(item: DateTimeOrDeltaValue) -> bool: return _DateTime[TValue, TInterface].AreEqual(self.GetValue(), item)
        
        return (isinstance(item, (IDate, ITime, IDateTime, ITimeDelta)) and equals(item.GetValue())) or (isinstance(item, (date, time, datetime, timedelta)) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue())
    
    def _CompareTo(self, item: TValue|TInterface|object) -> bool|None:
        def compareTo(item: TValue|TInterface) -> bool|None: return _DateTime[TValue, TInterface].Compare(self.GetValue(), item)
        
        return (isinstance(item, self._GetInterfaceType()) and compareTo(self._AsValue(item))) or (isinstance(item, self._GetValueType()) and compareTo(item))
    
    def ToString(self) -> str: return str(self.GetValue())
    
    @classmethod
    @abstractmethod
    def _GetValueType(cls) -> type[TValue]:
        ...
    @classmethod
    @abstractmethod
    def _GetInterfaceType(cls) -> type[TInterface]:
        ...
    
    @classmethod
    @final
    def _AreValuesEqual(cls, x: DateTimeOrDeltaValue, y: DateTimeOrDeltaValue) -> bool:
        return x == y
    @classmethod
    @abstractmethod
    def _CompareValues(cls, x: TValue, y: TValue) -> bool:
        ...
    
    @classmethod
    @abstractmethod
    def _AsValue(cls, item: TValue|TInterface) -> TValue:
        ...
    
    @classmethod
    @final
    def AsValue(cls, item: DateTimeOrDeltaValue|DateTimeOrDeltaItem) -> DateTimeOrDeltaValue:
        return item.GetValue() if isinstance(item, (IDate, ITime, IDateTime, ITimeDelta)) else item
    
    @classmethod
    @final
    def Compare(cls, x: TValue|TInterface, y: TValue|TInterface) -> bool|None:
        def compare(x: TValue, y: TValue) -> bool|None: return None if cls._AreValuesEqual(x, y) else cls._CompareValues(y, x)

        return compare(cls._AsValue(x), cls._AsValue(y))
    @classmethod
    @final
    def TryCompare(cls, x: TValue|TInterface|None, y: TValue|TInterface|None) -> bool|None:
        return y is None if x is None else (False if y is None else _DateTime[TValue, TInterface].Compare(x, y))

class Date(_DateTime[date, IDate], IDate):
    def __init__(self, value: date) -> None: super().__init__(value)
    
    @classmethod
    @final
    def _GetValueType(cls) -> type[date]:
        return date
    @classmethod
    @final
    def _GetInterfaceType(cls) -> type[IDate]:
        return IDate
    
    @classmethod
    @final
    def _AsValue(cls, item: date|IDate) -> date:
        return item.GetValue() if isinstance(item, IDate) else item
    @classmethod
    @final
    def _CompareValues(cls, x: date, y: date) -> bool:
        return x > y
class Time(_DateTime[time, ITime], ITime):
    def __init__(self, value: time) -> None: super().__init__(value)
    
    @classmethod
    @final
    def _GetValueType(cls) -> type[time]:
        return time
    @classmethod
    @final
    def _GetInterfaceType(cls) -> type[ITime]:
        return ITime
    
    @classmethod
    @final
    def _AsValue(cls, item: time|ITime) -> time:
        return item.GetValue() if isinstance(item, ITime) else item
    @classmethod
    @final
    def _CompareValues(cls, x: time, y: time) -> bool:
        return x > y
class DateTime(_DateTime[datetime, IDateTime], IDateTime):
    def __init__(self, value: datetime) -> None: super().__init__(value)
    
    @classmethod
    @final
    def _GetValueType(cls) -> type[datetime]:
        return datetime
    @classmethod
    @final
    def _GetInterfaceType(cls) -> type[IDateTime]:
        return IDateTime
    
    @classmethod
    @final
    def _AsValue(cls, item: datetime|IDateTime) -> datetime:
        return item.GetValue() if isinstance(item, IDateTime) else item
    @classmethod
    @final
    def _CompareValues(cls, x: datetime, y: datetime) -> bool:
        return x > y
class TimeDelta(_DateTime[timedelta, ITimeDelta], ITimeDelta):
    def __init__(self, value: timedelta) -> None: super().__init__(value)
    
    @classmethod
    @final
    def _GetValueType(cls) -> type[timedelta]:
        return timedelta
    @classmethod
    @final
    def _GetInterfaceType(cls) -> type[TimeDelta]:
        return TimeDelta
    
    @classmethod
    @final
    def _AsValue(cls, item: timedelta|ITimeDelta) -> timedelta:
        return item.GetValue() if isinstance(item, ITimeDelta) else item
    @classmethod
    @final
    def _CompareValues(cls, x: timedelta, y: timedelta) -> bool:
        return x > y

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self) -> None: super().__init__()

type PrimitiveValue = bool|NumericalValue|str|bytes

class PrimitiveType(IntEnum):
    Null = 0
    Bool = 1
    Integer = 2
    Floating = 3
    Decimal = 4
    String = 5
    Bytes = 6

    def TryMap(self) -> TypeBase[PrimitiveValue]|None:
        match self:
            case PrimitiveType.Bool: return bool
            case PrimitiveType.Integer: return int
            case PrimitiveType.Floating: return float
            case PrimitiveType.Decimal: return decimal
            case PrimitiveType.String: return str
            case PrimitiveType.Bytes: return bytes

            case _: return None
    def Map(self) -> TypeBase[PrimitiveValue]:
        result: TypeBase[PrimitiveValue]|None = self.TryMap()

        if result is None: raise ValueError(f"{self.name} is not supported.")

        return result

    @staticmethod
    def TryMapFromType[T: PrimitiveValue](t: TypeBase[T]|T) -> PrimitiveType:
        _t: TypeBase[T] = GetType(t)

        if _t == bool: return PrimitiveType.Bool
        if _t == int: return PrimitiveType.Integer
        if _t == float: return PrimitiveType.Floating
        if _t == decimal: return PrimitiveType.Decimal
        if _t == str: return PrimitiveType.String
        if _t == bytes: return PrimitiveType.Bytes

        return PrimitiveType.Null
    @staticmethod
    def MapFromType[T: PrimitiveValue](t: TypeBase[T]|T) -> PrimitiveType:
        result: PrimitiveType = PrimitiveType.TryMapFromType(t)

        if result == PrimitiveType.Null: raise ValueError(f"{GetTypeName(t)} is not supported.")

        return result

def TryMap(obj: object) -> IValueItem|None:
    match obj:
        case bool(): return GetTrueObject() if obj else GetFalseObject()
        case int(): return Integer(obj)
        case float(): return Float(obj)
        case decimal(): return Decimal(obj)
        case str(): return String(obj)
        case bytes(): return ByteArray(obj)
        case datetime(): return DateTime(obj)
        case date(): return Date(obj)
        case time(): return Time(obj)
        case timedelta(): return TimeDelta(obj)
        
        case _: return None
def Map(obj: object) -> IValueItem:
    result: IValueItem|None = TryMap(obj)

    if result is None: raise ValueError(f"{type(obj)} is not supported.")

    return result

class Finalizer(Abstract, IRemovable):
    def __init__(self, obj: object, action: Action) -> None:
        def remove() -> None:
            finalizer.detach()

            self.__remove = NoAction
        
        super().__init__()

        finalizer: finalize[Any, object] = finalize(obj, action)

        self.__remove: Action = remove # type: ignore[no-redef]
    
    def Remove(self) -> None: self.__remove()
class WeakReferenceFinalizer[T](Finalizer):
    def __init__(self, obj: T, action: Action) -> None:
        def tryGetValue() -> T|None: return _ref()

        super().__init__(obj, action)

        _ref: ReferenceType[T] = ref(obj)

        self.__tryGetValue: NullableFunction[T] = tryGetValue
    
    def TryGetValue(self) -> T|None: return self.__tryGetValue()
    
    def Remove(self) -> None:
        super().Remove()

        self.__tryGetValue = FuncNone
class DisposableFinalizer[T: IDisposableBase](WeakReferenceFinalizer[T], IDisposableBase):
    def __init__(self, obj: T, action: Action) -> None:
        def dispose() -> None:
            obj: IDisposableBase|None = self.TryGetValue()

            if obj is not None:
                obj.Dispose()

                self.Remove()

        super().__init__(obj, action)

        self.__dispose: Action = dispose
    
    def Remove(self) -> None:
        super().Remove()

        self.__dispose = NoAction
    
    def Dispose(self) -> None: self.__dispose()

class IWeakReferenceRegister[T: IDisposableBase](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetCookie(self) -> _WeakReference[T]:
        ...
    
    @abstractmethod
    def RegisterNode(self, node: IRemovable) -> None:
        ...

class IWeakReference[T](IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def TryGetValue(self) -> T|None: ...
    
    @abstractmethod
    def Invalidate(self) -> None: ...
@final
class _WeakReference[T: IDisposableBase](Abstract, IWeakReference[T]):
    @final
    class _Register[_T: IDisposableBase](Abstract, IWeakReferenceRegister[_T]):
        def __init__(self, obj: _T, cookie: _WeakReference[_T]) -> None:
            super().__init__()

            self.__obj: _T = obj
            self.__weakReference: _WeakReference[_T] = cookie
        
        def GetCookie(self) -> _WeakReference[_T]: return self.__weakReference
        
        def RegisterNode(self, node: IRemovable) -> None: self.__weakReference._RegisterNode(self.__obj, node)
    
    def __init__(self) -> None:
        super().__init__()

        self.__finalizer: DisposableFinalizer[T]|None = None
    
    def TryGetValue(self) -> T|None:
        finalizer: DisposableFinalizer[T]|None = self.__finalizer

        return None if finalizer is None else finalizer.TryGetValue()
    
    def Invalidate(self) -> None:
        finalizer: DisposableFinalizer[T]|None = self.__finalizer

        if finalizer is not None: finalizer.Dispose()
    
    def _RegisterNode(self, obj: T, node: IRemovable) -> None:
        self.__finalizer = DisposableFinalizer[T](obj, lambda: node.Remove())

    @staticmethod
    def _CreateRegister(obj: T) -> IWeakReferenceRegister[T]:
        return _WeakReference._Register[T](obj, _WeakReference[T]())

def CreateWeakReferenceRegister[T: IDisposableBase](obj: T) -> IWeakReferenceRegister[T]:
    return _WeakReference[T]._CreateRegister(obj) # pyright: ignore[reportPrivateUsage]