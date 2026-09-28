from typing import runtime_checkable, Protocol, Self

@runtime_checkable
class SupportsAnd(Protocol):
    def __and__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsOr(Protocol):
    def __or__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsXor(Protocol):
    def __xor__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsInversion(Protocol):
    def __invert__(self) -> Self: ...

@runtime_checkable
class SupportsLeftShift(Protocol):
    def __lshift__(self, other: int, /) -> Self: ...
@runtime_checkable
class SupportsRightShift(Protocol):
    def __rshift__(self, other: int, /) -> Self: ...

@runtime_checkable
class SupportsLogic(SupportsAnd, SupportsOr, SupportsXor, Protocol):
    pass
@runtime_checkable
class SupportsBasicBitwise(SupportsLogic, SupportsInversion, Protocol):
    pass

@runtime_checkable
class SupportsShift(SupportsLeftShift, SupportsRightShift, Protocol):
    pass

@runtime_checkable
class SupportsBitwise(SupportsBasicBitwise, SupportsShift, Protocol):
    pass

@runtime_checkable
class SupportsRAnd(Protocol):
    def __rand__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsROr(Protocol):
    def __ror__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsRXor(Protocol):
    def __rxor__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsRLeftShift(Protocol):
    def __rlshift__(self, other: int, /) -> Self: ...
@runtime_checkable
class SupportsRRightShift(Protocol):
    def __rrshift__(self, other: int, /) -> Self: ...

@runtime_checkable
class SupportsReflectedLogic(SupportsRAnd, SupportsROr, SupportsRXor, Protocol):
    pass
@runtime_checkable
class SupportsReflectedBasicBitwise(SupportsReflectedLogic, SupportsInversion, Protocol):
    pass

@runtime_checkable
class SupportsReflectedShift(SupportsRLeftShift, SupportsRRightShift, Protocol):
    pass

@runtime_checkable
class SupportsReflectedBitwise(SupportsReflectedBasicBitwise, SupportsReflectedShift, Protocol):
    pass

@runtime_checkable
class SupportsFullLogic(SupportsLogic, SupportsReflectedLogic, Protocol):
    pass
@runtime_checkable
class SupportsFullBasicBitwise(SupportsFullLogic, SupportsBasicBitwise, SupportsReflectedBasicBitwise, Protocol):
    pass

@runtime_checkable
class SupportsFullShift(SupportsShift, SupportsReflectedShift, Protocol):
    pass

@runtime_checkable
class SupportsFullBitwise(SupportsBitwise, SupportsReflectedBitwise, SupportsFullBasicBitwise, SupportsFullShift, Protocol):
    pass

type LogicProtocol = SupportsLogic|SupportsReflectedLogic
type ShiftProtocol = SupportsShift|SupportsReflectedShift

type BitwiseProtocol = SupportsBitwise|SupportsReflectedBitwise