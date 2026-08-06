from collections.abc import Iterable, Sequence, MutableSequence
from typing import overload, SupportsIndex

from WinCopies.Collections.Core import ITuple as ITupleBase, IList as IListBase
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple, IList
from WinCopies.Collections.Linked.Singly import ICountableQueue, CreateCountableQueue, CreateEnumerableStack
from WinCopies.Collections.Util import ReverseIndex

def GetAt[T](l: ITupleBase[T], index: SupportsIndex) -> T:
    return l.GetAt(int(index))

@overload
def GetValues[T](l: IList[T], index: slice) -> MutableSequence[T]: ...
@overload
def GetValues[T](l: ITuple[T], index: slice) -> Sequence[T]: ...

def GetValues[T](l: ITuple[T]|IList[T], index: slice) -> Sequence[T]|MutableSequence[T]:
    return l.SliceAt(index).AsSequence()

@overload
def GetItems[T](l: IList[T], index: SupportsIndex|slice) -> T|MutableSequence[T]: ...
@overload
def GetItems[T](l: ITuple[T], index: SupportsIndex|slice) -> T|Sequence[T]: ...

def GetItems[T](l: ITuple[T]|IList[T], index: SupportsIndex|slice) -> T|Sequence[T]|MutableSequence[T]:
    return GetAt(l, index) if isinstance(index, SupportsIndex) else GetValues(l, index)

@overload
def GetItemsAt[T](l: IList[T], index: SupportsIndex|slice) -> T|IList[T]: ...
@overload
def GetItemsAt[T](l: ITuple[T], index: SupportsIndex|slice) -> T|ITuple[T]: ...

def GetItemsAt[T](l: ITuple[T]|IList[T], index: SupportsIndex|slice) -> T|ITuple[T]|IList[T]:
    return GetAt(l, index) if isinstance(index, SupportsIndex) else l.SliceAt(index)

def SetValues[T](lst: IListBase[T], key: slice, values: Iterable[T]|ICountableEnumerable[T]) -> None:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, lst.GetCount())
    
    def getItems() -> tuple[Iterable[T], int]:
        match values:
            case ICountableEnumerable(): return (values.AsIterable(), values.GetCount())
            case Sequence(): return (values, len(values))

            case _:
                _values: ICountableQueue[T] = CreateCountableQueue(values)

                return (_values.AsGenerator(), _values.GetCount())

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

        lst.InsertRange(i, values.AsIterable() if isinstance(values, IEnumerable) else values)

    # step > 1
    elif i >= l: raise IndexError()

    else:
        items: tuple[Iterable[T], int] = getItems()

        if len(range(i, l, s)) != items[1]: raise ValueError()

        for item in items[0]:
            lst.SetAt(i, item)
            
            i += s
def SetItems[T](lst: IListBase[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex): lst.SetAt(int(index), value) # type: ignore
    else: SetValues(lst, index, value) # type: ignore

def RemoveValues[T](lst: IListBase[T], key: slice) -> None:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, lst.GetCount())

    s: int|None = key.step

    if s is None: s = 1
    elif s == 0: raise IndexError()
    
    i: int|None = key.start
    l: int|None = key.stop

    count: int = lst.GetCount()

    if i is None: i = 0
    if l is None: l = count

    if s < 0:
        RemoveValues(lst.AsReversed(), slice(reverseIndex(i), reverseIndex(l), -s))

        return

    if i >= l or i >= count: return

    if l >= count:
        if s == 1 and i == 0:
            lst.Clear()

            return

        l = count

    if s == 1: lst.RemoveRange(i, l - i)

    else:
        for index in CreateEnumerableStack(range(i, l, s)).AsIterable(): lst.RemoveAt(index)
def RemoveItems[T](lst: IListBase[T], index: SupportsIndex|slice) -> None:
    if isinstance(index, SupportsIndex): lst.RemoveAt(int(index))
    else: RemoveValues(lst, index)