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
from WinCopies.Typing import NumericalValue, IDisposable, INullable, IEnum
from WinCopies.Typing.Comparison import IHashableValue, IHashable, IExtendedHashableComparable, CompareTo
from WinCopies.Typing.Delegate import Action, NullableFunction
from WinCopies.Typing.Reflection import IsOf

class IItem(IHashableValue, IStringable):
    def __init__(self) -> None: super().__init__()

class IObject[T](IHashable[T], IItem):
    def __init__(self) -> None: super().__init__()
class Object[T](Abstract, IObject[T]):
    def __init__(self) -> None: super().__init__()

class IComparableObject[T](IObject[T], IExtendedHashableComparable[T]):
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
class IComparableComplexValueObject[TValue, TUnderlying, TObject](IComplexValueObject[TValue, TUnderlying, TObject], IComparableValueObject[TValue, TObject]):
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
    
    @staticmethod
    @abstractmethod
    def _AreValuesEqual(x: TObject, y: TObject) -> bool:
        ...
    
    @staticmethod
    @abstractmethod
    def AsValue(item: TValue|TObject|TInterface) -> TObject:
        ...
    
    @staticmethod
    @final
    def AreEqual(x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool:
        return ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(x) == ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(y)
    @staticmethod
    @final
    def TryAreEqual(x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool:
        return False if x is None or y is None else ExtendedValueObjectBase[TValue, TObject, TInterface].AreEqual(x, y)
class ComparableValueObjectBase[TValue, TObject, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TObject, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
    
    @staticmethod
    @abstractmethod
    def _CompareTo(x: TObject, y: TObject) -> bool:
        ...
    
    @staticmethod
    @final
    def Compare(x: TValue|TObject|TInterface, y: TValue|TObject|TInterface) -> bool|None:
        def compare(x: TObject, y: TObject) -> bool|None: return None if ComparableValueObjectBase[TValue, TObject, TInterface]._AreValuesEqual(x, y) else ComparableValueObjectBase[TValue, TObject, TInterface]._CompareTo(y, x)

        return compare(ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(x), ExtendedValueObjectBase[TValue, TObject, TInterface].AsValue(y))
    @staticmethod
    @final
    def TryCompare(x: TValue|TObject|TInterface|None, y: TValue|TObject|TInterface|None) -> bool|None:
        return y is None if x is None else (False if y is None else ComparableValueObjectBase[TValue, TObject, TInterface].Compare(x, y))

class ValueObject[TValue, TInterface: IValueItem](ExtendedValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
class ComparableValueObject[TValue, TInterface: IValueItem](ComparableValueObjectBase[TValue, TValue, TInterface]):
    def __init__(self, value: TValue) -> None: super().__init__(value)

class IBoolean(IComparableValueObject[bool, 'IBoolean|bool']):
    def __init__(self) -> None: super().__init__()
class __Boolean(Abstract, IBoolean):
    def __init__(self) -> None: super().__init__()
    
    def GetUnderlyingValue(self) -> bool: return self.GetValue()
    
    def Equals(self, item: IBoolean|bool|object) -> bool:
        def equals(item: bool) -> bool: return self.GetValue() == item
        
        return (isinstance(item, IBoolean) and equals(item.GetValue())) or (isinstance(item, bool) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue())
    
    def CompareTo(self, item: IBoolean|bool|object) -> bool|None:
        def compareTo(item: bool) -> bool|None: return CompareTo(self.GetValue(), item)
        
        return (isinstance(item, IBoolean) and compareTo(item.GetValue())) or (isinstance(item, bool) and compareTo(item))
    
    def ToString(self) -> str: return str(self.GetValue())

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

type NumericalObject = IInteger|IFloat|IDecimal
type Numerical = NumericalValue|NumericalObject

class INumericalItem(IValueItem):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def GetValue(self) -> NumericalValue:
        ...
class INumericalValue[T: NumericalValue](IComparableValueObject[T, Numerical], INumericalItem):
    def __init__(self) -> None: super().__init__()

class IInteger(INumericalValue[int]):
    def __init__(self) -> None: super().__init__()
class IFloat(INumericalValue[float]):
    def __init__(self) -> None: super().__init__()
class IDecimal(INumericalValue[decimal]):
    def __init__(self) -> None: super().__init__()

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
    
    def Equals(self, item: Numerical|object) -> bool: return Equals(self, item) if isinstance(item, INumericalItem) else ValueEquals(self, item)
    def Hash(self) -> int: return hash(self.GetValue())
    
    def CompareTo(self, item: Numerical|object) -> bool|None:
        def compareTo(item: int) -> bool|None: return CompareTo(self.GetValue(), item)
        
        return (isinstance(item, IInteger) and compareTo(item.GetValue())) or (isinstance(item, int) and compareTo(item))
    
    def ToString(self) -> str: return str(self.GetValue())
    
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
    def __init__(self, value: int) -> None: super().__init__(value)
    
    @staticmethod
    def FromEnum(value: Enum) -> IInteger:
        return Integer(value.value)
class Float(_NumericalValue[float], IFloat):
    def __init__(self, value: float) -> None: super().__init__(value)
class Decimal(_NumericalValue[decimal], IDecimal):
    def __init__(self, value: decimal) -> None: super().__init__(value)

class IEnumValue[T: Enum](IComparableComplexValueObject[T, int, IEnum|Enum], IEnum):
    def __init__(self) -> None: super().__init__()
class EnumValue[T: Enum](ValueObjectAbstract[T, int, IEnum|Enum], IEnumValue[T]):
    def __init__(self, value: T) -> None: super().__init__(value)
    
    @final
    def GetEnumValue(self) -> Enum:
        return self.GetValue()
    @final
    def GetUnderlyingValue(self) -> int:
        return int(self.GetValue().value)
    
    @final
    def IsSameAs(self, value: Enum) -> bool:
        return IsOf(self.GetValue(), type(value))
    
    def Equals(self, item: IEnum|Enum|object) -> bool:
        def equals(item: Enum) -> bool: return self.GetValue() == item
        
        return (isinstance(item, IEnum) and equals(item.GetEnumValue())) or (isinstance(item, Enum) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue().value)
    
    def CompareTo(self, item: IEnumValue[T]|Enum|object) -> bool|None:
        def compareTo(item: Enum) -> bool|None: return self.IsSameAs(item) and CompareTo(self.GetUnderlyingValue(), item.value)
        
        return (isinstance(item, IEnum) and compareTo(item.GetEnumValue())) or (isinstance(item, Enum) and compareTo(item))
    
    def ToString(self) -> str: return str(self.GetValue().name)

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
    def __init__(self) -> None: super().__init__()
class String(ComparableValueObject[str, IString], IString):
    def __init__(self, value: str) -> None: super().__init__(value)
    
    def Equals(self, item: IString|str|object) -> bool:
        def equals(item: str) -> bool: return String.AreEqual(self.GetValue(), item)
        
        return (isinstance(item, IString) and equals(item.GetValue())) or (isinstance(item, str) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue())
    
    def CompareTo(self, item: IString|str|object) -> bool|None:
        def compareTo(item: str) -> bool|None: return String.Compare(self.GetValue(), item)
        
        return (isinstance(item, IString) and compareTo(item.GetValue())) or (isinstance(item, str) and compareTo(item))
    
    def ToString(self) -> str: return self.GetValue()
    
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

class IByteArray(IItemObject[bytes, 'IByteArray']):
    def __init__(self) -> None: super().__init__()
class ByteArray(ComparableValueObject[bytes, IByteArray], IByteArray):
    def __init__(self, value: bytes) -> None: super().__init__(value)
    
    def Equals(self, item: IByteArray|bytes|object) -> bool:
        def equals(item: bytes) -> bool: return ByteArray.AreEqual(self.GetValue(), item)
        
        return (isinstance(item, IByteArray) and equals(item.GetValue())) or (isinstance(item, bytes) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue())
    
    def CompareTo(self, item: IByteArray|bytes|object) -> bool|None:
        def compareTo(item: bytes) -> bool|None: return ByteArray.Compare(self.GetValue(), item)
        
        return (isinstance(item, IByteArray) and compareTo(item.GetValue())) or (isinstance(item, bytes) and compareTo(item))
    
    def ToString(self) -> str: return super(IInterface, self).__str__()
    
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

class IType[T](IItemObject[type[T], 'IType[T]']):
    def __init__(self) -> None: super().__init__()
class Type[T](ValueObjectBase[type[T], IType[T]], IType[T]):
    def __init__(self, t: type[T]) -> None: super().__init__(t)
    
    def Equals(self, item: IType[T]|type[T]|object) -> bool:
        def equals(item: type) -> bool: return self.GetValue() == item
        
        return (isinstance(item, IType) and equals(item.GetValue())) or (isinstance(item, type) and equals(item)) # pyright: ignore[reportUnknownArgumentType]
    def Hash(self) -> int: return hash(self.GetValue())
    
    def ToString(self) -> str: return str(self.GetValue())
    
    @staticmethod
    def Create(value: T) -> IType[T]:
        return Type[T](type(value))

class IReference[T](IItemObject[T, 'IReference[T]']):
    def __init__(self) -> None: super().__init__()

class Reference[T](ValueObjectBase[T, IReference[T]], IReference[T]):
    def __init__(self, parameter: T) -> None: super().__init__(parameter)
    
    def Equals(self, item: IReference[T]|object) -> bool:
        def equals(item: Any) -> bool: return self.GetValue() is item
        
        return equals(item.GetValue()) if isinstance(item, IReference) else equals(item)
    def Hash(self) -> int: return hash(id(self.GetValue()))
class DefaultReference[T](Reference[T]):
    def __init__(self, parameter: T) -> None: super().__init__(parameter)
    
    def ToString(self) -> str: return str(self)

type DateOrTimeValue = date|time
type DateAndTimeValue = DateOrTimeValue|datetime
type DateTimeOrDeltaValue = DateAndTimeValue|timedelta

type DateOrTimeItem = IDate|ITime
type DateAndTimeItem = DateOrTimeItem|IDateTime
type DateTimeOrDeltaItem = DateAndTimeItem|ITimeDelta

type DateOrTime = DateOrTimeValue|DateOrTimeItem
type DateAndTime = DateOrTime|DateAndTimeValue|DateAndTimeItem
type DateTimeOrDelta = DateAndTime|DateTimeOrDeltaValue|DateTimeOrDeltaItem

class IDate(IItemObject[date, "time|datetime|timedelta|DateTimeOrDeltaItem"], IComparable["date|DateTimeOrDeltaItem"]):
    def __init__(self) -> None: super().__init__()
class ITime(IItemObject[time, "date|datetime|timedelta|DateTimeOrDeltaItem"], IComparable["time|DateTimeOrDeltaItem"]):
    def __init__(self) -> None: super().__init__()
class IDateTime(IItemObject[datetime, "DateOrTimeValue|timedelta|DateTimeOrDeltaItem"], IComparable["datetime|DateTimeOrDeltaItem"]):
    def __init__(self) -> None: super().__init__()
class ITimeDelta(IItemObject[timedelta, "DateAndTimeValue|DateTimeOrDeltaItem"], IComparable["timedelta|DateTimeOrDeltaItem"]):
    def __init__(self) -> None: super().__init__()

class _DateTime[TValue: DateTimeOrDeltaValue, TInterface: DateTimeOrDeltaItem](ExtendedValueObjectBase[TValue, DateTimeOrDeltaValue, DateTimeOrDeltaItem]):
    def __init__(self, value: TValue) -> None: super().__init__(value)
    
    def Equals(self, item: TValue|TInterface|object) -> bool:
        def equals(item: DateTimeOrDeltaValue) -> bool: return _DateTime[TValue, TInterface].AreEqual(self.GetValue(), item)
        
        return (isinstance(item, (IDate, ITime, IDateTime, ITimeDelta)) and equals(item.GetValue())) or (isinstance(item, (date, time, datetime, timedelta)) and equals(item))
    def Hash(self) -> int: return hash(self.GetValue())
    
    def CompareTo(self, item: TValue|TInterface|object) -> bool|None:
        def compareTo(item: TValue|TInterface) -> bool|None: return _DateTime[TValue, TInterface].Compare(self.GetValue(), item)
        
        return (isinstance(item, _DateTime[TValue, TInterface]._GetInterfaceType()) and compareTo(_DateTime[TValue, TInterface]._AsValue(item))) or (isinstance(item, _DateTime[TValue, TInterface]._GetValueType()) and compareTo(item))
    
    def ToString(self) -> str: return str(self.GetValue())
    
    @staticmethod
    @abstractmethod
    def _GetValueType() -> type[TValue]:
        pass
    @staticmethod
    @abstractmethod
    def _GetInterfaceType() -> type[TInterface]:
        pass
    
    @staticmethod
    @final
    def _AreValuesEqual(x: DateTimeOrDeltaValue, y: DateTimeOrDeltaValue) -> bool:
        return x == y
    @staticmethod
    @abstractmethod
    def _CompareTo(x: TValue, y: TValue) -> bool:
        pass
    
    @staticmethod
    @abstractmethod
    def _AsValue(item: TValue|TInterface) -> TValue:
        pass
    
    @staticmethod
    @final
    def AsValue(item: DateTimeOrDeltaValue|DateTimeOrDeltaItem) -> DateTimeOrDeltaValue:
        return item.GetValue() if isinstance(item, (IDate, ITime, IDateTime, ITimeDelta)) else item
    
    @staticmethod
    @final
    def Compare(x: TValue|TInterface, y: TValue|TInterface) -> bool|None:
        def compare(x: TValue, y: TValue) -> bool|None: return None if _DateTime[TValue, TInterface]._AreValuesEqual(x, y) else _DateTime[TValue, TInterface]._CompareTo(y, x)

        return compare(_DateTime[TValue, TInterface]._AsValue(x), _DateTime[TValue, TInterface]._AsValue(y))
    @staticmethod
    @final
    def TryCompare(x: TValue|TInterface|None, y: TValue|TInterface|None) -> bool|None:
        return y is None if x is None else (False if y is None else _DateTime[TValue, TInterface].Compare(x, y))

class Date(_DateTime[date, IDate], IDate):
    def __init__(self, value: date) -> None: super().__init__(value)
    
    @staticmethod
    @final
    def _GetValueType() -> type[date]:
        return date
    @staticmethod
    @final
    def _GetInterfaceType() -> type[IDate]:
        return IDate
    
    @staticmethod
    @final
    def _AsValue(item: date|IDate) -> date:
        return item.GetValue() if isinstance(item, IDate) else item
    @staticmethod
    @final
    def _CompareTo(x: date, y: date) -> bool:
        return x > y
class Time(_DateTime[time, ITime], ITime):
    def __init__(self, value: time) -> None: super().__init__(value)
    
    @staticmethod
    @final
    def _GetValueType() -> type[time]:
        return time
    @staticmethod
    @final
    def _GetInterfaceType() -> type[ITime]:
        return ITime
    
    @staticmethod
    @final
    def _AsValue(item: time|ITime) -> time:
        return item.GetValue() if isinstance(item, ITime) else item
    @staticmethod
    @final
    def _CompareTo(x: time, y: time) -> bool:
        return x > y
class DateTime(_DateTime[datetime, IDateTime], IDateTime):
    def __init__(self, value: datetime) -> None: super().__init__(value)
    
    @staticmethod
    @final
    def _GetValueType() -> type[datetime]:
        return datetime
    @staticmethod
    @final
    def _GetInterfaceType() -> type[IDateTime]:
        return IDateTime
    
    @staticmethod
    @final
    def _AsValue(item: datetime|IDateTime) -> datetime:
        return item.GetValue() if isinstance(item, IDateTime) else item
    @staticmethod
    @final
    def _CompareTo(x: datetime, y: datetime) -> bool:
        return x > y
class TimeDelta(_DateTime[timedelta, ITimeDelta], ITimeDelta):
    def __init__(self, value: timedelta) -> None: super().__init__(value)
    
    @staticmethod
    @final
    def _GetValueType() -> type[timedelta]:
        return timedelta
    @staticmethod
    @final
    def _GetInterfaceType() -> type[TimeDelta]:
        return TimeDelta
    
    @staticmethod
    @final
    def _AsValue(item: timedelta|ITimeDelta) -> timedelta:
        return item.GetValue() if isinstance(item, ITimeDelta) else item
    @staticmethod
    @final
    def _CompareTo(x: timedelta, y: timedelta) -> bool:
        return x > y

class IDisposableObject[T](IDisposable, IObject[T]):
    def __init__(self) -> None: super().__init__()

class PrimitiveType(Enum):
    Null = 0
    Bool = 1
    Integer = 2
    Floating = 3
    Decimal = 4
    String = 5
    Bytes = 6

    def TryMap(self) -> type|None:
        match self:
            case PrimitiveType.Bool: return bool
            case PrimitiveType.Integer: return int
            case PrimitiveType.Floating: return float
            case PrimitiveType.Decimal: return decimal
            case PrimitiveType.String: return str
            case PrimitiveType.Bytes: return bytes

            case _: return None
    def Map(self) -> type:
        result: type|None = self.TryMap()

        if result is None: raise ValueError(f"{self.name} is not supported.")

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