from collections.abc import Iterable, Sequence
from typing import SupportsIndex

from WinCopies.Collections.Abstraction.Collection import CreateTuple
from WinCopies.Collections.Core import IList
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple
from WinCopies.Collections.Linked.Singly import CreateCountableQueue, CreateEnumerableStack
from WinCopies.Collections.Util import ReverseIndex

def GetItems[T](l: ITuple[T], index: SupportsIndex|slice) -> T|Sequence[T]:
    return l.GetAt(int(index)) if isinstance(index, SupportsIndex) else l.SliceAt(index).AsSequence()

def SetValues[T](lst: IList[T], key: slice, values: Iterable[T]) -> None:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, lst.GetCount())
    
    def getItems() -> ICountableEnumerable[T]: return (values
                                               if isinstance(values, ICountableEnumerable)
                                               else (CreateTuple(values) if isinstance(values, Sequence)
                                               else CreateCountableQueue(values).AsCountableGenerator()))

    s: int|None = key.step

    if s is None: s = 1
    
    elif s == 0: raise IndexError()

    i: int|None = key.start
    l: int|None = key.stop

    if i is None: i = 0
    
    if l is None: l = lst.GetCount()

    if s < 0: SetValues(lst.AsReversed(), slice(reverseIndex(i), reverseIndex(l), -s), values)

    elif s == 1:
        if i > l: raise IndexError()

        count: int = l - i

        if count > 0: lst.RemoveRange(i, count)

        lst.InsertRange(i, values)

    # step > 1
    elif i >= l: raise IndexError()

    items: ICountableEnumerable[T] = getItems()

    if len(range(i, l, s)) != items.GetCount(): raise ValueError()

    for item in items.AsIterable():
        lst.SetAt(i, item)
        
        i += s
def SetItems[T](lst: IList[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex): lst.SetAt(int(index), value) # type: ignore
    
    else: SetValues(lst, index, value) # type: ignore

def RemoveValues[T](lst: IList[T], key: slice) -> None:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, lst.GetCount())

    s: int|None = key.step

    if s is None: s = 1
    elif s == 0: raise IndexError()
    
    i: int|None = key.start
    l: int|None = key.stop

    if i is None: i = 0
    if l is None: l = lst.GetCount()

    if s < 0:
        RemoveValues(lst.AsReversed(), slice(reverseIndex(i), reverseIndex(l), -s))

        return

    if i >= l: raise IndexError()
    
    for index in CreateEnumerableStack(range(i, l, s)): lst.RemoveAt(index)
def RemoveItems[T](lst: IList[T], index: SupportsIndex|slice) -> None:
    if isinstance(index, SupportsIndex): lst.RemoveAt(int(index))
    else: RemoveValues(lst, index)