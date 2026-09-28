from __future__ import annotations

from collections.abc import Iterable
from enum import (_EnumDict, # pyright: ignore[reportPrivateUsage]
                  EnumMeta as _EnumMeta, Enum as _Enum, FlagBoundary,
                  Flag as _Flag,
                  IntEnum as _IntEnum, StrEnum as _StrEnum)
from types import DynamicClassAttribute
from typing import final, Any, Generic, Self, Type, TypeVar, cast

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Typing import IEnum
from WinCopies.Typing.Comparison import IEquatableObjectBase, IHashable, IHashableComparable
from WinCopies.Typing.Operand.Arithmetic import IAdditionableItem
from WinCopies.Typing.Operand.Bitwise import IBitwiseItem
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsEqualityAndRichComparison

_T = TypeVar('_T')
_U = TypeVar('_U', bound=SupportsEqualityComparison)
_V = TypeVar('_V', bound=SupportsEqualityAndRichComparison)

type EquatableEnumProtocol = IntegerEnum|UnorderedIntEnum|StringEnum
type ComparableEnumProtocol = IntegerEnum

_TEquatableEnum = TypeVar('_TEquatableEnum', bound=EquatableEnumProtocol)
_TComparableEnum = TypeVar('_TComparableEnum', bound=ComparableEnumProtocol)

class IEquatableEnum[TEnum: EquatableEnumProtocol, TValue: SupportsEqualityComparison](IEnum[TEnum], IHashable[TValue]):
    def __init__(self) -> None: super().__init__()
class IComparableEnum[TEnum: ComparableEnumProtocol, TValue: SupportsEqualityAndRichComparison](IEquatableEnum[TEnum, TValue], IHashableComparable[TValue]):
    def __init__(self) -> None: super().__init__()

class _EnumTypeBase(type, Iterable["Any"]):
    def __init__(self, name: str, bases: ReadOnlyArray[type], dict: dict[str, Any], /, **kwds: Any) -> None: super().__init__(name, bases, dict, **kwds)
    def __new__(cls: type[_EnumTypeBase], name: str, bases: ReadOnlyArray[type], namespace: dict[str, Any], /, **kwds: Any) -> Any: return super().__new__(cls, name, bases, namespace, **kwds)
class _EnumType(_EnumTypeBase, _EnumMeta):
    def __init__(self, name: str, bases: ReadOnlyArray[type], dict: dict[str, Any], /, **kwds: Any) -> None: # pyright: ignore[reportInconsistentConstructor]
        super().__init__(name, bases, dict, **kwds)

    def __new__(metacls: type[_EnumType], cls: str, bases: ReadOnlyArray[type], classdict: _EnumDict, *, boundary: FlagBoundary|None = None, _simple: bool = False, **kwds: Any) -> Any:
        return super().__new__(metacls, cls, bases, classdict, boundary=boundary, _simple=_simple, **kwds)

class EnumBase(IEquatableObjectBase[_T], metaclass=_EnumTypeBase):
    def __init__(self, value: _T|Self) -> None: super().__init__()

    @classmethod
    @final
    def ValidateValueType(cls, value: _T|object) -> bool:
        type: Type[_T] = cls._GetComparableType()
        
        return isinstance(value, type)
    @classmethod
    @final
    def CheckValueType(cls, value: _T|object) -> None:
        if not cls.ValidateValueType(value): raise TypeError(f"{cls.__name__}: value {value!r} is not an {type}.")

    def __new__(cls, value: _T|Self) -> Self:
        if isinstance(value, cls): value = value.value
        
        cls.CheckValueType(value)
        
        member: Self = object.__new__(cls)
        member._value_ = cast(_T, value)

        return member

    _value_: _T

    @DynamicClassAttribute
    def value(self) -> _T:
        return self._value_

class Enum(EnumBase[_T]):
    def __init__(self, value: _T|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _T|Self) -> Self: return super().__new__(cls, value)

    _name_: str

    @DynamicClassAttribute
    def name(self) -> str:
        return self._name_
class Flag(EnumBase[_T]):
    def __init__(self, value: _T|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _T|Self) -> Self: return super().__new__(cls, value)

    _name_: str|None

    @DynamicClassAttribute
    def name(self) -> str|None:
        return self._name_

class EquatableEnumBase(Generic[_TEquatableEnum, _U], EnumBase[_U], IEquatableEnum[_TEquatableEnum, _U]):
    def __init__(self, value: _U|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _U|Self) -> Self: return super().__new__(cls, value)

    @final
    def _AsComparableValue(self) -> _U: return self.value
class EquatableEnum(EquatableEnumBase[_TEquatableEnum, _U], Enum[_U]):
    def __init__(self, value: _U|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _U|Self) -> Self: return super().__new__(cls, value)
class EquatableFlag(EquatableEnumBase[_TEquatableEnum, _U], Flag[_U]):
    def __init__(self, value: _U|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _U|Self) -> Self: return super().__new__(cls, value)

class OrderedEnumBase(EquatableEnumBase[_TComparableEnum, _V], IComparableEnum[_TComparableEnum, _V]):
    def __init__(self, value: _V|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _V|Self) -> Self: return super().__new__(cls, value)
class OrderedEnum(OrderedEnumBase[_TComparableEnum, _V], EquatableEnum[_TComparableEnum, _V]):
    def __init__(self, value: _V|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _V|Self) -> Self: return super().__new__(cls, value)
class OrderedFlag(OrderedEnumBase[_TComparableEnum, _V], EquatableFlag[_TComparableEnum, _V]):
    def __init__(self, value: _V|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: _V|Self) -> Self: return super().__new__(cls, value)

class _EnumBase(_Enum, metaclass=_EnumType):
    def __init__(self) -> None: super().__init__()
class _FlagBase(_Flag, metaclass=_EnumType):
    def __init__(self) -> None: super().__init__()

class IntFlag(OrderedFlag["IntFlag", int], IAdditionableItem["IntFlag", int], IBitwiseItem["IntFlag", int], _FlagBase): # type: ignore[misc]
    def __init__(self, value: int|Self) -> None: super().__init__(value)

    def __new__(cls, value: int|Self) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[int]: return int

    @final
    def GetEnumValue(self) -> IntFlag: return self

class UnorderedIntEnum(EquatableEnum["UnorderedIntEnum", int], _EnumBase):
    def __init__(self, value: int|Self) -> None: super().__init__(value)

    def __new__(cls, value: int|Self) -> Self: return super().__new__(cls, value)

    @final
    def GetEnumValue(self) -> UnorderedIntEnum: return self
class IntEnum(OrderedEnum["IntEnum", int], IAdditionableItem["IntEnum", int], _EnumBase):
    def __init__(self, value: int|Self) -> None: super().__init__(value)

    def __new__(cls, value: int|Self) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[int]: return int

    @final
    def GetEnumValue(self) -> IntEnum: return self

    @final
    def _GetArithmeticValue(self) -> int: return self.value

    @final
    def _CreateNew(self, value: int) -> IntEnum: return type(self)(value)
class StrEnum(EquatableEnum["StrEnum", str], _EnumBase):
    def __init__(self, value: str|Self) -> None: super().__init__(value)
    
    def __new__(cls, value: str|Self) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[str]: return str

    @final
    def GetEnumValue(self) -> StrEnum: return self

type IntegerEnum = IntEnum|IntFlag|_IntEnum
type StringEnum = StrEnum|_StrEnum

type TypedEnum = IntegerEnum|StringEnum