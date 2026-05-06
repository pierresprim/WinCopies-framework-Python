from abc import abstractmethod
from typing import final, runtime_checkable, Any, Protocol

from WinCopies import IInterface

class IEquatableValue(IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: object) -> bool:
        pass
    
    @final
    def __eq__(self, value: object) -> bool:
        return self.Equals(value)
class IEquatableItem(IEquatableValue):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Hash(self) -> int:
        pass

    @final
    def __hash__(self) -> int:
        return self.Hash()

class IEquatable[T](IInterface):
    def __init__(self) -> None:
        super().__init__()
    
    @abstractmethod
    def Equals(self, item: T) -> bool:
        pass
class IEquatableObject[T](IEquatable[T|object], IEquatableValue):
    def __init__(self) -> None:
        super().__init__()

@runtime_checkable
class SupportsRichComparison(Protocol):
    """Protocol for types that support comparison operators."""
    
    def __lt__(self, other: Any, /) -> bool:
        """Less than comparison."""
        ...
    
    def __le__(self, other: Any, /) -> bool:
        """Less than or equal comparison."""
        ...
    
    def __gt__(self, other: Any, /) -> bool:
        """Greater than comparison."""
        ...
    
    def __ge__(self, other: Any, /) -> bool:
        """Greater than or equal comparison."""
        ...

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
class IComparableItem(IComparableValue, IEquatableItem):
    def __init__(self) -> None:
        super().__init__()
class IComparable[T](IInterface):
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
class IComparableObject[T](IComparable[T|object], IComparableValue, IEquatableObject[T]):
    def __init__(self) -> None:
        super().__init__()

type IComparableProtocol = IComparableValue|SupportsRichComparison