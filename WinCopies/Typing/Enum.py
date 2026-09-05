from __future__ import annotations

from enum import Enum as _Enum, IntEnum as _IntEnum, StrEnum as _StrEnum
from types import DynamicClassAttribute
from typing import final, Generic, Self, Type, TypeVar

from WinCopies.Typing import IEnum
from WinCopies.Typing.Comparison import IEquatableObjectBase, IHashable, IHashableComparable
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsEqualityAndRichComparison

_T = TypeVar('_T')
_U = TypeVar('_U', bound=SupportsEqualityComparison)
_V = TypeVar('_V', bound=SupportsEqualityAndRichComparison)

type EquatableEnumProtocol = IntegerEnum|StringEnum
type ComparableEnumProtocol = IntegerEnum

_TEquatableEnum = TypeVar('_TEquatableEnum', bound=EquatableEnumProtocol)
_TComparableEnum = TypeVar('_TComparableEnum', bound=ComparableEnumProtocol)

class IEquatableEnum[TEnum: EquatableEnumProtocol, TValue: SupportsEqualityComparison](IEnum[TEnum], IHashable[TValue]):
    def __init__(self) -> None: super().__init__()
class IComparableEnum[TEnum: ComparableEnumProtocol, TValue: SupportsEqualityAndRichComparison](IEquatableEnum[TEnum, TValue], IHashableComparable[TValue]):
    def __init__(self) -> None: super().__init__()

class Enum(IEquatableObjectBase[_T]):
    def __init__(self, value: _T) -> None: super().__init__()

    @classmethod
    @final
    def ValidateValueType(cls, value: _T|object) -> bool:
        type: Type[_T] = cls._GetComparableType()
        
        return isinstance(value, type)
    @classmethod
    @final
    def CheckValueType(cls, value: _T|object) -> None:
        if not cls.ValidateValueType(value): raise TypeError(f"{cls.__name__}: value {value!r} is not an {type}.")

    def __new__(cls, value: _T) -> Self:
        cls.CheckValueType(value)
        
        member: Self = object.__new__(cls)
        member._value_ = value

        return member

    _name_: str
    _value_: _T

    @DynamicClassAttribute
    def name(self) -> str:
        return self._name_
    @DynamicClassAttribute
    def value(self) -> _T:
        return self._value_
class EquatableEnum(Generic[_TEquatableEnum, _U], Enum[_U], IEquatableEnum[_TEquatableEnum, _U]):
    def __init__(self, value: _U) -> None: super().__init__(value)
    
    def __new__(cls, value: _U) -> Self: return super().__new__(cls, value)

    @final
    def _AsComparableValue(self) -> _U: return self.value
class OrderedEnum(Generic[_TComparableEnum, _V], EquatableEnum[_TComparableEnum, _V], IComparableEnum[_TComparableEnum, _V]):
    def __init__(self, value: _V) -> None: super().__init__(value)
    
    def __new__(cls, value: _V) -> Self: return super().__new__(cls, value)

class IntEnum(OrderedEnum["IntEnum", int], _Enum):
    def __init__(self, value: int) -> None: super().__init__(value)

    def __new__(cls, value: int) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[int]: return int

    @final
    def GetEnumValue(self) -> IntEnum: return self
class StrEnum(EquatableEnum["StrEnum", str], _Enum):
    def __init__(self, value: str) -> None: super().__init__(value)
    
    def __new__(cls, value: str) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[str]: return str

    @final
    def GetEnumValue(self) -> StrEnum: return self

type IntegerEnum = IntEnum|_IntEnum
type StringEnum = StrEnum|_StrEnum