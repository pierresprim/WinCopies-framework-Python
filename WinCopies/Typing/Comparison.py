from abc import abstractmethod
from typing import final, Self, Type

from WinCopies import IInterface, IsTruthy, IsFalsy
from WinCopies.Delegates import BoolFalse
from WinCopies.Typing.Delegate import Function, Converter
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsRichComparison, SupportsEqualityAndRichComparison

class IEquatableBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Equals(self, item: Self|object) -> bool:
        ...
class IHashableBase(IInterface):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        ...

class _IEquatable[T](IEquatableBase):
    def __init__(self) -> None: super().__init__()
    
    @abstractmethod
    def Equals(self, item: Self|T|object) -> bool:
        ...
    
    @final
    def __eq__(self, value: Self|T|object, /) -> bool: return self.Equals(value)

class _IHashable(IHashableBase):
    def __init__(self) -> None: super().__init__()

    @final
    def __hash__(self, /) -> int: return self.Hash()
class _INotHashable(IInterface):
    def __init__(self) -> None: super().__init__()
    
    __hash__ = None # type: ignore

class IEquatableValue(_IEquatable[object]):
    def __init__(self) -> None: super().__init__()
class IEquatableItem[T](_IEquatable[T]):
    def __init__(self) -> None: super().__init__()

 # _IHashable must be inherited first to avoid auto dunder suppression when inheriting from _IEquatable
 
class IHashableValue(_IHashable, IEquatableValue):
    def __init__(self) -> None: super().__init__()
class IHashableItem[T](_IHashable, IEquatableItem[T]):
    def __init__(self) -> None: super().__init__()

class INotHashableValue(IEquatableValue, _INotHashable):
    def __init__(self) -> None: super().__init__()
class INotHashableItem[T](IEquatableItem[T], _INotHashable):
    def __init__(self) -> None: super().__init__()

class IComparableBase[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _AsComparableValue(self) -> T:
        ...

class _IComparable[T](IInterface):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _Compare[TResult](self, item: Self|T, predicate: Converter[T, TResult], onError: Function[TResult]) -> TResult:
        ...
class _IRichComparable[TItem, TValue](_IComparable[TValue], IComparableBase[TValue]):
    def __init__(self) -> None: super().__init__()

    @final
    def _AsFromSameInterface(self, other: Self|TItem|object) -> Self|None: return other if isinstance(other, type(self)) else None
    
    @abstractmethod
    def _CompareToValue[TResult](self, item: TValue|object, predicate: Converter[TValue, TResult], onError: Function[TResult]) -> TResult:
        ...

    @final
    def _Compare[TResult](self, item: Self|TValue|object, predicate: Converter[TValue, TResult], onError: Function[TResult]) -> TResult:
        other: Self|None = self._AsFromSameInterface(item)
        
        return self._CompareToValue(item, predicate, onError) if other is None else predicate(other._AsComparableValue())

class IEquatableObjectAbstract[T](IEquatableItem[T]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @abstractmethod
    def _GetComparableType(cls) -> Type[T]:
        ...
class IEquatableObjectBase[T](IEquatableObjectAbstract[T], IComparableBase[T]):
    def __init__(self) -> None: super().__init__()

class IEquatableValueBase[TItem, TValue](IEquatableItem[TItem], _IRichComparable[TItem, TValue]):
    def __init__(self) -> None: super().__init__()
    
    def Equals(self, item: Self|TItem|object) -> bool:
        return self._Compare(item, lambda other: self._AsComparableValue() == other, BoolFalse)
class IEquatableItemBase[T](IEquatableValueBase[T, T|object]):
    def __init__(self) -> None: super().__init__()

    def _CompareToValue[TResult](self, item: T|object, predicate: Converter[T|object, TResult], onError: Function[TResult]) -> TResult: return predicate(item)

class IEquatable[T](IEquatableObjectBase[T], IEquatableValueBase[T, T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _CompareToValue[TResult](self, item: T|object, predicate: Converter[T, TResult], onError: Function[TResult]) -> TResult:
        if isinstance(item, self._GetComparableType()): return predicate(item)
        
        return onError()

class IHashableValueBase[TItem, TValue](IHashableItem[TItem], IEquatableValueBase[TItem, TValue]):
    def __init__(self) -> None: super().__init__()

    def Hash(self) -> int: return hash(self._AsComparableValue())
class IHashableItemBase[T](IHashableValueBase[T, T|object], IEquatableItemBase[T]):
    def __init__(self) -> None: super().__init__()

    def Hash(self) -> int: return hash(self._AsComparableValue())

class IHashable[T](IHashableValueBase[T, T], IEquatable[T]):
    def __init__(self) -> None: super().__init__()

class _IComparableValue[T](IEquatableValue, _IComparable[T]):
    def __init__(self) -> None: super().__init__()

    @classmethod
    @abstractmethod
    def _GetComparableType(cls) -> Type[T]:
        ...
    
    @abstractmethod
    def _CompareTo(self, item: T) -> bool|None:
        ...
    
    @final
    def CompareTo(self, item: Self|T) -> bool|None:
        def onError() -> None: raise NotImplementedError()

        return self._Compare(item, self._CompareTo, onError)
    
    @final
    def IsLessThan(self, other: Self|T) -> bool:
        """Less than comparison."""
        return self.CompareTo(other) is False
    
    @final
    def IsLessThanOrEqual(self, other: Self|T) -> bool:
        """Less than or equal comparison."""
        return IsFalsy(self.CompareTo(other))
    
    @final
    def IsGreaterThan(self, other: Self|T) -> bool:
        """Greater than comparison."""
        return IsTruthy(self.CompareTo(other))
    
    @final
    def IsGreaterThanOrEqual(self, other: Self|T) -> bool:
        """Greater than or equal comparison."""
        return self.CompareTo(other) is not False
    
    @final
    def __lt__(self, other: Self|T, /) -> bool:
        """Less than comparison."""
        return self.IsLessThan(other)
    
    @final
    def __le__(self, other: Self|T, /) -> bool:
        """Less than or equal comparison."""
        return self.IsLessThanOrEqual(other)
    
    @final
    def __gt__(self, other: Self|T, /) -> bool:
        """Greater than comparison."""
        return self.IsGreaterThan(other)
    
    @final
    def __ge__(self, other: Self|T, /) -> bool:
        """Greater than or equal comparison."""
        return self.IsGreaterThanOrEqual(other)

class IComparableValue[T](_IComparableValue[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _Compare[TResult](self, item: Self|T|object, predicate: Converter[T, TResult], onError: Function[TResult]) -> TResult:
        return predicate(item) if isinstance(item, type(self)) and isinstance(item, self._GetComparableType()) else onError()
class IHashableComparableValue[T](IHashableValue, IComparableValue[T]):
    def __init__(self) -> None: super().__init__()

class IComparableObject[T](_IComparableValue[T]):
    def __init__(self) -> None: super().__init__()

    @final
    def _Compare[TResult](self, item: Self|T|object, predicate: Converter[T, TResult], onError: Function[TResult]) -> TResult:
        return predicate(item) if isinstance(item, self._GetComparableType()) else onError()
class IHashableComparableObject[T](IHashableValue, IComparableObject[T]):
    def __init__(self) -> None: super().__init__()

class IComparableItemBase[TItem: HashableProtocol, TValue](IEquatableItem[TItem], _IRichComparable[TItem, TValue]):
    def __init__(self) -> None: super().__init__()

    @abstractmethod
    def _CompareTo(self, item: TValue) -> bool|None:
        ...
    
    @final
    def CompareTo(self, item: Self|TItem) -> bool|None:
        def onError() -> None: raise NotImplementedError()

        return self._Compare(item, self._CompareTo, onError)
    
    @final
    def IsLessThan(self, other: Self|TItem) -> bool:
        """Less than comparison."""
        return self.CompareTo(other) is False
    
    @final
    def IsLessThanOrEqual(self, other: Self|TItem) -> bool:
        """Less than or equal comparison."""
        return IsFalsy(self.CompareTo(other))
    
    @final
    def IsGreaterThan(self, other: Self|TItem) -> bool:
        """Greater than comparison."""
        return IsTruthy(self.CompareTo(other))
    
    @final
    def IsGreaterThanOrEqual(self, other: Self|TItem) -> bool:
        """Greater than or equal comparison."""
        return self.CompareTo(other) is not False
    
    @final
    def __lt__(self, other: Self|TItem, /) -> bool:
        """Less than comparison."""
        return self.IsLessThan(other)
    
    @final
    def __le__(self, other: Self|TItem, /) -> bool:
        """Less than or equal comparison."""
        return self.IsLessThanOrEqual(other)
    
    @final
    def __gt__(self, other: Self|TItem, /) -> bool:
        """Greater than comparison."""
        return self.IsGreaterThan(other)
    
    @final
    def __ge__(self, other: Self|TItem, /) -> bool:
        """Greater than or equal comparison."""
        return self.IsGreaterThanOrEqual(other)
class IComparableItem[T: HashableProtocol](IComparableItemBase[T, T]):
    def __init__(self) -> None: super().__init__()

class IHashableComparableItem[T](IComparableItemBase[T, T|object], IHashableItemBase[T]):
    def __init__(self) -> None: super().__init__()
class IHashableComparable[T: SupportsEqualityAndRichComparison](IComparableItem[T], IHashable[T]):
    def __init__(self) -> None: super().__init__()

    def _CompareTo(self, item: T) -> bool|None: return CompareTo(self._AsComparableValue(), item)

type EquatableProtocol = IEquatableValue|SupportsEqualityComparison
type HashableProtocol = IHashableValue|SupportsEqualityComparison

def __Check(x: SupportsRichComparison, y: SupportsRichComparison, b: bool) -> bool:
    return x <= y if b else x < y

def Between[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(x, value, bx) and __Check(value, y, by)
def Outside[T: SupportsRichComparison](x: T, value: T, y: T, bx: bool = True, by: bool = True) -> bool:
    return __Check(value, x, bx) or __Check(y, value, by)

def Equals(x: SupportsEqualityComparison, y: SupportsEqualityComparison) -> bool:
    return x == y

def CompareFrom(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x < y
def CompareTo(x: SupportsRichComparison, y: SupportsRichComparison) -> bool|None:
    return None if x == y else x > y