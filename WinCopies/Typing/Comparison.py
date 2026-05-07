from abc import abstractmethod
from typing import final, Any

from WinCopies import IInterface
from WinCopies.Typing.Protocols import SupportsEqualityComparison, SupportsRichComparison

class _IHashableBase(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        pass
class _IHashable(_IHashableBase):
    def __init__(self) -> None:
        super().__init__()

    @final
    def __hash__(self) -> int:
        return self.Hash()
class _INotHashable(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    __hash__ = None # type: ignore

class IEquatableValue(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: object) -> bool:
        pass
    
    @final
    def __eq__(self, value: object) -> bool:
        return self.Equals(value)
class IEquatableItem[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: T) -> bool:
        pass
class IEquatable[T](IEquatableItem[T|object], IEquatableValue):
    def __init__(self) -> None:
        super().__init__()

class IHashableValue(_IHashable, IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
class IHashableItem[T](IEquatableItem[T], _IHashableBase):
    def __init__(self) -> None:
        super().__init__()
class IHashable[T](IEquatable[T], IHashableItem[T|object], IHashableValue):
    def __init__(self) -> None:
        super().__init__()

class INotHashableValue(IEquatableValue, _INotHashable):
    def __init__(self) -> None:
        super().__init__()
class INotHashableItem[T](IEquatableItem[T], _INotHashable):
    def __init__(self) -> None:
        super().__init__()

class IComparableValue(IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsLessThan(self, other: object) -> bool:
        """Less than comparison."""
        pass
    
    @abstractmethod
    def IsLessThanOrEqual(self, other: object) -> bool:
        """Less than or equal comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThan(self, other: object) -> bool:
        """Greater than comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThanOrEqual(self, other: object) -> bool:
        """Greater than or equal comparison."""
        pass
    
    @final
    def __lt__(self, other: Any, /) -> bool:
        """Less than comparison."""
        return self.IsLessThan(other)
    
    @final
    def __le__(self, other: Any, /) -> bool:
        """Less than or equal comparison."""
        return self.IsLessThanOrEqual(other)
    
    @final
    def __gt__(self, other: Any, /) -> bool:
        """Greater than comparison."""
        return self.IsGreaterThan(other)
    
    @final
    def __ge__(self, other: Any, /) -> bool:
        """Greater than or equal comparison."""
        return self.IsGreaterThanOrEqual(other)
class IExtendedComparableValue(IComparableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CompareTo(self, item: object) -> bool|None:
        pass

class IHashableComparableValue(IComparableValue, IHashableValue):
    def __init__(self) -> None:
        super().__init__()
class IExtendedHashableComparableValue(IExtendedComparableValue, IHashableComparableValue):
    def __init__(self) -> None:
        super().__init__()

class IComparableItem[T](IEquatableItem[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def IsLessThan(self, other: T) -> bool:
        """Less than comparison."""
        pass
    
    @abstractmethod
    def IsLessThanOrEqual(self, other: T) -> bool:
        """Less than or equal comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThan(self, other: T) -> bool:
        """Greater than comparison."""
        pass
    
    @abstractmethod
    def IsGreaterThanOrEqual(self, other: T) -> bool:
        """Greater than or equal comparison."""
        pass
class IExtendedComparableItem[T](IComparableItem[T]):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def CompareTo(self, item: T) -> bool|None:
        pass
    
    @final
    def IsLessThan(self, other: T) -> bool:
        """Less than comparison."""
        return self.CompareTo(other) is False
    
    @final
    def IsLessThanOrEqual(self, other: T) -> bool:
        """Less than or equal comparison."""
        return self.CompareTo(other) is not True
    
    @final
    def IsGreaterThan(self, other: T) -> bool:
        """Greater than comparison."""
        return self.CompareTo(other) is True
    
    @final
    def IsGreaterThanOrEqual(self, other: T) -> bool:
        """Greater than or equal comparison."""
        return self.CompareTo(other) is not False

class IHashableComparableItem[T](IComparableItem[T], IHashableItem[T]):
    def __init__(self) -> None:
        super().__init__()
class IExtendedHashableComparableItem[T](IExtendedComparableItem[T], IHashableComparableItem[T]):
    def __init__(self) -> None:
        super().__init__()

class IComparable[T](IComparableItem[T|object], IComparableValue):
    def __init__(self) -> None:
        super().__init__()
class IExtendedComparable[T](IComparable[T], IExtendedComparableItem[T|object], IExtendedComparableValue):
    def __init__(self) -> None:
        super().__init__()

class IHashableComparable[T](IComparable[T], IHashable[T], IHashableComparableItem[T|object], IHashableComparableValue):
    def __init__(self) -> None:
        super().__init__()
class IExtendedHashableComparable[T](IHashableComparable[T], IExtendedComparable[T], IExtendedHashableComparableItem[T|object], IExtendedHashableComparableValue):
    def __init__(self) -> None:
        super().__init__()

type EqualityComparableProtocol = IEquatableValue|SupportsEqualityComparison
type ComparableProtocol = IComparableValue|SupportsRichComparison