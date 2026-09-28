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
class SupportsLeftShift(Protocol):
    def __lshift__(self, other: int, /) -> Self: ...
@runtime_checkable
class SupportsRightShift(Protocol):
    def __rshift__(self, other: int, /) -> Self: ...

@runtime_checkable
class SupportsLogic(SupportsAnd, SupportsOr, SupportsXor, Protocol):
    pass
@runtime_checkable
class SupportsShift(SupportsLeftShift, SupportsRightShift, Protocol):
    pass

@runtime_checkable
class SupportsBitwise(SupportsLogic, SupportsShift, Protocol):
    pass

@runtime_checkable
class SupportsRAnd(Protocol):
    def __and__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsROr(Protocol):
    def __or__(self, other: Self, /) -> Self: ...
@runtime_checkable
class SupportsRXor(Protocol):
    def __xor__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsRLeftShift(Protocol):
    def __lshift__(self, other: int, /) -> Self: ...
@runtime_checkable
class SupportsRRightShift(Protocol):
    def __rshift__(self, other: int, /) -> Self: ...

@runtime_checkable
class SupportsReflectedLogic(SupportsRAnd, SupportsROr, SupportsRXor, Protocol):
    pass
@runtime_checkable
class SupportsReflectedShift(SupportsRLeftShift, SupportsRRightShift, Protocol):
    pass

@runtime_checkable
class SupportsReflectedBitwise(SupportsReflectedLogic, SupportsReflectedShift, Protocol):
    pass

@runtime_checkable
class SupportsFullBitwise(SupportsBitwise, SupportsReflectedBitwise, Protocol):
    pass

type LogicProtocol = SupportsLogic|SupportsReflectedLogic
type ShiftProtocol = SupportsShift|SupportsReflectedShift

type BitwiseProtocol = SupportsBitwise|SupportsReflectedBitwise