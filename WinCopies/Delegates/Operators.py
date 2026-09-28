from typing import overload, Any

from WinCopies.Typing.Protocols.Arithmetic import SupportsAdd, SupportsSub
from WinCopies.Typing.Protocols.Bitwise import SupportsAnd, SupportsOr, SupportsXor, SupportsLeftShift, SupportsRightShift
from WinCopies.Typing.Protocols.Generic.Arithmetic import (SupportsAdd as _SupportsAdd, SupportsSub as _SupportsSub,
                                                           SupportsRAdd as _SupportsRAdd, SupportsRSub as _SupportsRSub)
from WinCopies.Typing.Protocols.Generic.Bitwise import (SupportsAnd as _SupportsAnd, SupportsOr as _SupportsOr, SupportsXor as _SupportsXor,
                                                        SupportsRAnd as _SupportsRAnd, SupportsROr as _SupportsROr, SupportsRXor as _SupportsRXor,

                                                        SupportsLeftShift as _SupportsLeftShift, SupportsRightShift as _SupportsRightShift,
                                                        SupportsRLeftShift as _SupportsRLeftShift, SupportsRRightShift as _SupportsRRightShift)

# The homogeneous overload comes first: for a type variable bounded by a Self-typed protocol (such as `TValue: SupportsBitwise`), mypy binds `Self` to the bound,
# so the reflected overloads alone would type `And(value, value)` as the bound rather than as the type variable.

@overload
def Add[T: SupportsAdd](x: T, y: T, /) -> T: ...
@overload
def Add[TOther, TResult](x: _SupportsAdd[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def Add[TOther, TResult](x: TOther, y: _SupportsRAdd[TOther, TResult], /) -> TResult: ...
def Add(x: Any, y: Any, /) -> Any: return x + y

@overload
def Sub[T: SupportsSub](x: T, y: T, /) -> T: ...
@overload
def Sub[TOther, TResult](x: _SupportsSub[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def Sub[TOther, TResult](x: TOther, y: _SupportsRSub[TOther, TResult], /) -> TResult: ...
def Sub(x: Any, y: Any, /) -> Any: return x - y

@overload
def And[T: SupportsAnd](x: T, y: T, /) -> T: ...
@overload
def And[TOther, TResult](x: _SupportsAnd[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def And[TOther, TResult](x: TOther, y: _SupportsRAnd[TOther, TResult], /) -> TResult: ...
def And(x: Any, y: Any, /) -> Any: return x & y

@overload
def Or[T: SupportsOr](x: T, y: T, /) -> T: ...
@overload
def Or[TOther, TResult](x: _SupportsOr[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def Or[TOther, TResult](x: TOther, y: _SupportsROr[TOther, TResult], /) -> TResult: ...
def Or(x: Any, y: Any, /) -> Any: return x | y

@overload
def Xor[T: SupportsXor](x: T, y: T, /) -> T: ...
@overload
def Xor[TOther, TResult](x: _SupportsXor[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def Xor[TOther, TResult](x: TOther, y: _SupportsRXor[TOther, TResult], /) -> TResult: ...
def Xor(x: Any, y: Any, /) -> Any: return x ^ y

@overload
def LeftShift[T: SupportsLeftShift](x: T, y: int, /) -> T: ...
@overload
def LeftShift[TOther, TResult](x: _SupportsLeftShift[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def LeftShift[TOther, TResult](x: TOther, y: _SupportsRLeftShift[TOther, TResult], /) -> TResult: ...
def LeftShift(x: Any, y: Any, /) -> Any: return x << y

@overload
def RightShift[T: SupportsRightShift](x: T, y: int, /) -> T: ...
@overload
def RightShift[TOther, TResult](x: _SupportsRightShift[TOther, TResult], y: TOther, /) -> TResult: ...
@overload
def RightShift[TOther, TResult](x: TOther, y: _SupportsRRightShift[TOther, TResult], /) -> TResult: ...
def RightShift(x: Any, y: Any, /) -> Any: return x >> y