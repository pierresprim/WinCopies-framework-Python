from typing import runtime_checkable, Protocol, Self

@runtime_checkable
class SupportsLogic(Protocol):
    def __and__(self, other: Self, /) -> Self: ...
    def __or__(self, other: Self, /) -> Self: ...
    def __xor__(self, other: Self, /) -> Self: ...

@runtime_checkable
class SupportsShift(Protocol):
    def __lshift__(self, other: int, /) -> Self: ...
    def __rshift__(self, other: int, /) -> Self: ...

@runtime_checkable
class SupportsBitwise(SupportsLogic, SupportsShift, Protocol):
    pass

@runtime_checkable
class SupportsAnd[TOther, TResult](Protocol):
    def __and__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRAnd[TOther, TResult](Protocol):
    def __rand__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsOr[TOther, TResult](Protocol):
    def __or__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsROr[TOther, TResult](Protocol):
    def __ror__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsXor[TOther, TResult](Protocol):
    def __xor__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRXor[TOther, TResult](Protocol):
    def __rxor__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsLShift[TOther, TResult](Protocol):
    def __lshift__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRLShift[TOther, TResult](Protocol):
    def __rlshift__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsRShift[TOther, TResult](Protocol):
    def __rshift__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRRShift[TOther, TResult](Protocol):
    def __rrshift__(self, other: TOther, /) -> TResult: ...