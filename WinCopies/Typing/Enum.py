from enum import Enum as _Enum, IntEnum as _IntEnum, StrEnum as _StrEnum
from types import DynamicClassAttribute
from typing import final, Self, Type, TypeVar

from WinCopies.Typing.Comparison import IEquatableObjectBase, IHashable, IHashableComparable
from WinCopies.Typing.Protocols import SupportsEqualityAndRichComparison

T = TypeVar('T')
U = TypeVar('U', bound=SupportsEqualityAndRichComparison)

class Enum(IEquatableObjectBase[T]):
    def __init__(self, value: T) -> None: super().__init__()

    def __new__(cls, value: T) -> Self:
        type: Type[T] = cls._GetComparableType()
        
        if not isinstance(value, type): raise TypeError(f"{cls.__name__}: value {value!r} is not an {type}.") # pyright: ignore[reportUnnecessaryIsInstance]
        
        member: Self = object.__new__(cls)
        member._value_ = value

        return member

    _value_: T

    @DynamicClassAttribute
    def value(self) -> T:
        return self._value_
class ComparableEnum(Enum[U], IHashable[U]):
    def __init__(self, value: U) -> None: super().__init__(value)
    
    def __new__(cls, value: U) -> Self: return super().__new__(cls, value)

    @final
    def _AsComparableValue(self) -> U: return self.value
class OrderedEnum(ComparableEnum[U], IHashableComparable[U]):
    def __init__(self, value: U) -> None: super().__init__(value)
    
    def __new__(cls, value: U) -> Self: return super().__new__(cls, value)

class IntEnum(OrderedEnum[int], _Enum):
    def __init__(self, value: int) -> None: super().__init__(value)

    def __new__(cls, value: int) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[int]: return int
class StrEnum(ComparableEnum[str], _Enum):
    def __init__(self, value: str) -> None: super().__init__(value)
    
    def __new__(cls, value: str) -> Self: return super().__new__(cls, value)

    @classmethod
    @final
    def _GetComparableType(cls) -> Type[str]: return str

type IntegerEnum = IntEnum|_IntEnum
type StringEnum = StrEnum|_StrEnum