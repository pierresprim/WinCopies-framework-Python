from __future__ import annotations

from collections.abc import Iterable

from WinCopies.Bool import BooleanableEnum, NullableBoolean
from WinCopies.Collections.Enumeration import IEnumerable, IReversableEnumerable
from WinCopies.Collections.Linked.Singly import CreateStack, CreateEnumerableStack

class IterableScanResult(BooleanableEnum):
    DoesNotExist = -2
    Empty = -1
    Success = 0
    Error = 1
    
    def Not(self) -> IterableScanResult: return (IterableScanResult.Error if self == IterableScanResult.Success else IterableScanResult.Success) if self else self
class ScanResult(BooleanableEnum):
    Error = -1
    Success = 0
    Empty = 1
    Null = 2
    
    def ToNullableBool(self) -> bool|None: return True if self == ScanResult.Success else (None if self.value > 0 else False)
    
    def ToNullableBoolean(self) -> NullableBoolean: return NullableBoolean.BoolTrue if self == ScanResult.Success else (NullableBoolean.Null if self.value > 0 else NullableBoolean.BoolFalse)

def GetReversed[T](items: Iterable[T]) -> IEnumerable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items) if isinstance(items, IReversableEnumerable) else CreateEnumerableStack(items)
def Reverse[T](items: Iterable[T]) -> Iterable[T]:
    def enumerate(items: IReversableEnumerable[T]) -> IEnumerable[T]: return items.AsReversed()
    
    return enumerate(items).AsIterable() if isinstance(items, IReversableEnumerable) else CreateStack(items).AsGenerator()