from typing import runtime_checkable, Any, Protocol, Self

@runtime_checkable
class SupportsEqualityComparison(Protocol):
    """Protocol for types that support equality comparison operator."""
    
    def __eq__(self, other: Any, /) -> bool:
        ...
    def __hash__(self, /) -> int:
        ...
@runtime_checkable
class SupportsRichComparison(Protocol):
    """Protocol for types that support comparison operators."""
    
    def __lt__(self, other: Self, /) -> bool:
        """Less than comparison."""
        ...
    def __le__(self, other: Self, /) -> bool:
        """Less than or equal comparison."""
        ...
    def __gt__(self, other: Self, /) -> bool:
        """Greater than comparison."""
        ...
    def __ge__(self, other: Self, /) -> bool:
        """Greater than or equal comparison."""
        ...

@runtime_checkable
class SupportsEqualityAndRichComparison(Protocol):
    def __eq__(self, other: Any, /) -> bool:
        ...
    def __hash__(self, /) -> int:
        ...
    
    def __lt__(self, other: Self, /) -> bool:
        """Less than comparison."""
        ...
    def __le__(self, other: Self, /) -> bool:
        """Less than or equal comparison."""
        ...
    def __gt__(self, other: Self, /) -> bool:
        """Greater than comparison."""
        ...
    def __ge__(self, other: Self, /) -> bool:
        """Greater than or equal comparison."""
        ...