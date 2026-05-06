from typing import runtime_checkable, Any, Protocol

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