from WinCopies.Typing.Protocols.Bitwise import SupportsLogic, SupportsShift

def And[T: SupportsLogic](x: T, y: T, /) -> T: return x & y
def Or[T: SupportsLogic](x: T, y: T, /) -> T: return x | y
def Xor[T: SupportsLogic](x: T, y: T, /) -> T: return x ^ y

def LeftShift[T: SupportsShift](x: T, y: int, /) -> T: return x << y
def RightShift[T: SupportsShift](x: T, y: int, /) -> T: return x >> y