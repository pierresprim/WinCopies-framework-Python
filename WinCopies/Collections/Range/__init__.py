from collections.abc import Iterable, Sequence, MutableSequence
from typing import overload, SupportsIndex

from WinCopies.Collections.Abstraction.Collection import CreateTuple
from WinCopies.Collections.Core import ITuple as ITupleBase, IList as IListBase
from WinCopies.Collections.Enumeration import IEnumerable, ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple, IList
from WinCopies.Collections.Linked.Singly import CreateCountableQueue, CreateEnumerableStack
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
    
    def getItems() -> ICountableEnumerable[T]:
        match values:
            case ICountableEnumerable(): return values
            case Sequence(): return CreateTuple(values)

            case _: return CreateCountableQueue(values).AsCountableGenerator()

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
        items: ICountableEnumerable[T] = getItems()

        if len(range(i, l, s)) != items.GetCount(): raise ValueError()

        for item in items.AsIterable():
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

    if s == 1:
        if i == 0 and l >= count: lst.Clear()
        else: lst.RemoveRange(i, None if l > count - i else l)

        return
    
    for index in CreateEnumerableStack(range(i, l, s)).AsIterable(): lst.RemoveAt(index)
def RemoveItems[T](lst: IListBase[T], index: SupportsIndex|slice) -> None:
    if isinstance(index, SupportsIndex): lst.RemoveAt(int(index))
    else: RemoveValues(lst, index)