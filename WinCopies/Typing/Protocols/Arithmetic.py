from typing import runtime_checkable, Protocol, Self

@runtime_checkable
class SupportsAdd(Protocol):
    def __add__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsSub(Protocol):
    def __sub__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsAddSub(SupportsAdd, SupportsSub, Protocol):
    pass

@runtime_checkable
class SupportsPos(Protocol):
    def __pos__(self, /) -> Self: ...
@runtime_checkable
class SupportsNeg(Protocol):
    def __neg__(self, /) -> Self: ...

@runtime_checkable
class SupportsPosNeg(SupportsPos, SupportsNeg, Protocol):
    pass

@runtime_checkable
class SupportsMul(Protocol):
    def __mul__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsDiv(Protocol):
    def __truediv__(self, other: Self, /) -> Self: ...
    def __floordiv__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsMod(Protocol):
    def __mod__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsMulDivMod(SupportsMul, SupportsDiv, SupportsMod, Protocol):
    pass

@runtime_checkable
class SupportsBasicArithmetic(SupportsAddSub, SupportsPosNeg, SupportsMulDivMod, Protocol):
    pass

@runtime_checkable
class SupportsPower(Protocol):
    def __pow__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsArithmetic(SupportsBasicArithmetic, SupportsPower, Protocol):
    pass

@runtime_checkable
class SupportsRAdd(Protocol):
    def __radd__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsRSub(Protocol):
    def __rsub__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsReflectedAddSub(SupportsRAdd, SupportsRSub, Protocol):
    pass

@runtime_checkable
class SupportsRMul(Protocol):
    def __rmul__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsRDiv(Protocol):
    def __rtruediv__(self, other: Self, /) -> Self: ...
    def __rfloordiv__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsRMod(Protocol):
    def __rmod__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsReflectedMulDivMod(SupportsRMul, SupportsRDiv, SupportsRMod, Protocol):
    pass

@runtime_checkable
class SupportsReflectedBasicArithmetic(SupportsReflectedAddSub, SupportsPosNeg, SupportsReflectedMulDivMod, Protocol):
    pass

@runtime_checkable
class SupportsRPower(Protocol):
    def __rpow__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsReflectedArithmetic(SupportsReflectedBasicArithmetic, SupportsRPower, Protocol):
    pass

@runtime_checkable
class SupportsFullAddSub(SupportsAddSub, SupportsReflectedAddSub, Protocol):
    pass
@runtime_checkable
class SupportsFullMulDivMod(SupportsMulDivMod, SupportsReflectedMulDivMod, Protocol):
    pass

@runtime_checkable
class SupportsFullBasicArithmetic(SupportsBasicArithmetic, SupportsReflectedBasicArithmetic, SupportsFullAddSub, SupportsFullMulDivMod, Protocol):
    pass

@runtime_checkable
class SupportsFullArithmetic(SupportsArithmetic, SupportsReflectedArithmetic, SupportsFullBasicArithmetic, Protocol):
    pass

type AddSubProtocol = SupportsAddSub|SupportsReflectedAddSub
type MulDivModProtocol = SupportsMulDivMod|SupportsReflectedMulDivMod

type BasicArithmeticProtocol = SupportsBasicArithmetic|SupportsReflectedBasicArithmetic|AddSubProtocol|MulDivModProtocol
type ArithmeticProtocol = SupportsArithmetic|SupportsReflectedArithmetic|BasicArithmeticProtocol