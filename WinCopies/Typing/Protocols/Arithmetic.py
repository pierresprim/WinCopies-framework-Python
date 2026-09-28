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
class SupportsPosNeg(Protocol):
    def __pos__(self, /) -> Self: ...
    def __neg__(self, /) -> Self: ...

@runtime_checkable
class SupportsMulDivMod(Protocol):
    def __mul__(self, other: Self, /) -> Self: ...
    def __truediv__(self, other: Self, /) -> Self: ...
    def __floordiv__(self, other: Self, /) -> Self: ...
    def __mod__(self, other: Self, /) -> Self: ...

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
class SupportsFullAddSub(SupportsAddSub, SupportsReflectedAddSub, Protocol):
    pass

type AddSubProtocol = SupportsAddSub|SupportsReflectedAddSub