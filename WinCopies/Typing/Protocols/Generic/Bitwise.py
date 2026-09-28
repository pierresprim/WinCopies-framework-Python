from typing import runtime_checkable, Protocol

@runtime_checkable
class SupportsAnd[TOther, TResult](Protocol):
    def __and__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsOr[TOther, TResult](Protocol):
    def __or__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsXor[TOther, TResult](Protocol):
    def __xor__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsLeftShift[TOther, TResult](Protocol):
    def __lshift__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRightShift[TOther, TResult](Protocol):
    def __rshift__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsRAnd[TOther, TResult](Protocol):
    def __rand__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsROr[TOther, TResult](Protocol):
    def __ror__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRXor[TOther, TResult](Protocol):
    def __rxor__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsRLeftShift[TOther, TResult](Protocol):
    def __rlshift__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRRightShift[TOther, TResult](Protocol):
    def __rrshift__(self, other: TOther, /) -> TResult: ...