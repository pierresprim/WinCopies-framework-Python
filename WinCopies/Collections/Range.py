from collections.abc import Iterable, Sequence
from typing import SupportsIndex

from WinCopies.Collections import IList, ReverseIndex
from WinCopies.Collections.Abstraction.Collection import Tuple
from WinCopies.Collections.Enumeration import ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple
from WinCopies.Collections.Linked.Singly import CountableQueue, EnumerableStack

def GetItems[T](l: ITuple[T], index: SupportsIndex|slice) -> T|Sequence[T]:
    return l.GetAt(int(index)) if isinstance(index, SupportsIndex) else l.SliceAt(index).AsSequence()

def SetValues[T](lst: IList[T], key: slice, values: Iterable[T]) -> None:
    def reverseIndex(index: int) -> int:
        return ReverseIndex(index, lst.GetCount())
    def replace(i: int, l: int, s: int) -> None:
        def getItems() -> ICountableEnumerable[T]:
            if isinstance(values, ICountableEnumerable):
                return values
            elif isinstance(values, Sequence):
                return Tuple[T](values)
            
            return CountableQueue[T](*values).AsCountableGenerator()
        
        def getRangeCount(start: int, stop: int, step: int) -> int:
            count: int = 0

            for _ in range(start, stop, step):
                count += 1
            
            return count
        
        items: ICountableEnumerable[T]|None = getItems()
        
        if getRangeCount(i, l, s) == items.GetCount():
            for item in items.AsIterable():
                lst.SetAt(i, item)

                i += s

        else:
            raise ValueError()

    s: int = key.step

    if s == 0:
        raise IndexError()
    
    i: int = key.start
    l: int = key.stop

    if s < 0:
        SetValues(lst.AsReversed(), slice(reverseIndex(i), reverseIndex(l), -s), values)

        return

    if i > l:
        raise IndexError()
    
    if s == 1:
        if i == l:
            for item in values:
                lst.Insert(i, item)

                i += 1
        
        else:
            replace(i, l, 1)
    
    if i == l:
        raise IndexError()
    
    replace(i, l, s)
def SetItems[T](lst: IList[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex):
        if isinstance(value, Iterable):
            raise ValueError()
        
        lst.SetAt(int(index), value)
    
    else:
        SetValues(lst, index, value) # type: ignore


def RemoveValues[T](lst: IList[T], key: slice) -> None:
    def reverseIndex(index: int) -> int:
        return ReverseIndex(index, lst.GetCount())

    s: int = key.step

    if s == 0:
        raise IndexError()
    
    i: int = key.start
    l: int = key.stop

    if s < 0:
        RemoveValues(lst.AsReversed(), slice(reverseIndex(i), reverseIndex(l), -s))

        return

    if i >= l:
        raise IndexError()
    
    for index in EnumerableStack(*range(i, l, s)):
        lst.RemoveAt(index)
def RemoveItems[T](lst: IList[T], index: SupportsIndex|slice) -> None:
    if isinstance(index, SupportsIndex):
        lst.RemoveAt(int(index))
    
    else:
        RemoveValues(lst, index)