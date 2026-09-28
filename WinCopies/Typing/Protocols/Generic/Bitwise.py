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
class SupportsLogic[TOther, TResult](SupportsAnd[TOther, TResult], SupportsOr[TOther, TResult], SupportsXor[TOther, TResult], Protocol):
    pass
@runtime_checkable
class SupportsShift[TOther, TResult](SupportsLeftShift[TOther, TResult], SupportsRightShift[TOther, TResult], Protocol):
    pass

@runtime_checkable
class SupportsBitwise[TOther, TResult](SupportsLogic[TOther, TResult], SupportsShift[TOther, TResult], Protocol):
    pass

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

@runtime_checkable
class SupportsReflectedLogic[TOther, TResult](SupportsRAnd[TOther, TResult], SupportsROr[TOther, TResult], SupportsRXor[TOther, TResult], Protocol):
    pass
@runtime_checkable
class SupportsReflectedShift[TOther, TResult](SupportsRLeftShift[TOther, TResult], SupportsRRightShift[TOther, TResult], Protocol):
    pass

@runtime_checkable
class SupportsReflectedBitwise[TOther, TResult](SupportsReflectedLogic[TOther, TResult], SupportsReflectedShift[TOther, TResult], Protocol):
    pass