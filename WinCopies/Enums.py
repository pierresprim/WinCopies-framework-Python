from enum import Enum

from WinCopies.Typing.Enum import IntEnum

class Endianness(Enum):
    Null = 0
    Little = 1
    Big = 2

class Sign(Enum):
    Signed = 1
    Unsigned = 2
    Float = 3

class BitDepthLevel(IntEnum):
    One = 8
    Two = 16
    Three = 32
    Four = 64