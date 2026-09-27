from typing import runtime_checkable, Protocol, Self

@runtime_checkable
class SupportsAddSub(Protocol):
    def __add__(self, other: Self, /) -> Self: ...
    def __sub__(self, other: Self, /) -> Self: ...

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