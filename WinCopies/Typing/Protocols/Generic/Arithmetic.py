from typing import runtime_checkable, Protocol

@runtime_checkable
class SupportsAdd[TOther, TResult](Protocol):
    def __add__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsSub[TOther, TResult](Protocol):
    def __sub__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsAddSub[TOther, TResult](SupportsAdd[TOther, TResult], SupportsSub[TOther, TResult], Protocol):
    pass

@runtime_checkable
class SupportsRAdd[TOther, TResult](Protocol):
    def __radd__(self, other: TOther, /) -> TResult: ...
@runtime_checkable
class SupportsRSub[TOther, TResult](Protocol):
    def __rsub__(self, other: TOther, /) -> TResult: ...

@runtime_checkable
class SupportsReflectedAddSub[TOther, TResult](SupportsRAdd[TOther, TResult], SupportsRSub[TOther, TResult], Protocol):
    pass

@runtime_checkable
class SupportsFullAddSub[TOther, TResult](SupportsAddSub[TOther, TResult], SupportsReflectedAddSub[TOther, TResult], Protocol):
    pass

type AddSubProtocol[TOther, TResult] = SupportsAddSub[TOther, TResult]|SupportsReflectedAddSub[TOther, TResult]