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
    One = 8
    Two = One << 1
    Three = One << 2
    Four = One << 3
    Five = One << 4
    Six = One << 5
    Seven = One << 6
    Eight = One << 7
    Nine = One << 8
    Ten = One << 9

class ErrorMessages(StrEnum):
    ReentrancyNotAllowed = "Reentrant calls are not supported: this method cannot be called while another operation is in progress on this object."