from collections.abc import Sequence
from enum import auto

from WinCopies.Typing.Enum import IntEnum, StrEnum

class Endianness(IntEnum):
    Null = 0
    Little = 1
    Big = 2

class Sign(IntEnum):
    Signed = 1
    Unsigned = 2
    Float = 3

class BitDepthLevel(IntEnum):
    @staticmethod
    def _generate_next_value_(name: str, start: int, count: int, last_values: Sequence[int]) -> int:
        return 8 << count
    
    One = auto()
    Two = auto()
    Three = auto()
    Four = auto()
    Five = auto()
    Six = auto()
    Seven = auto()
    Eight = auto()
    Nine = auto()
    Ten = auto()

class ErrorMessages(StrEnum):
    ReentrancyNotAllowed = "Reentrant calls are not supported: this method cannot be called while another operation is in progress on this object."