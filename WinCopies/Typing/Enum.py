from enum import Enum
from typing import Self

from WinCopies.Typing.Reflection import AreFromSameClass

class OrderedEnum(Enum):
    def __lt__(self, other: Self) -> bool:
        """Less than comparison."""

        return self.value < other.value if AreFromSameClass(self, other) else NotImplemented
    def __le__(self, other: Self) -> bool:
        """Less than or equal comparison."""

        return self.value <= other.value if AreFromSameClass(self, other) else NotImplemented
    
    def __gt__(self, other: Self) -> bool:
        """Greater than comparison."""

        return self.value > other.value if AreFromSameClass(self, other) else NotImplemented
    def __ge__(self, other: Self) -> bool:
        """Greater than or equal comparison."""

        return self.value >= other.value if AreFromSameClass(self, other) else NotImplemented