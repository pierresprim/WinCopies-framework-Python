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

def __Normalize(index: int, count: int) -> int: return count + index

# A negative step runs down to 0, so -1 marks the position just past it.
def __GetDefaultStart(count: int, step: int) -> int: return count - 1 if step < 0 else 0
def __GetDefaultStop(count: int, step: int) -> int: return -1 if step < 0 else count

def __ResolveIndex(index: int, count: int, step: int) -> int:
    return index if index >= 0 else max(__Normalize(index, count), __GetDefaultStop(count, step) if step < 0 else 0)

def __ResolveBounds(key: slice, count: int, step: int) -> tuple[int, int]:
    def resolve(index: int|None, default: int) -> int:
        return default if index is None else __ResolveIndex(index, count, step)

    return (resolve(key.start, __GetDefaultStart(count, step)), resolve(key.stop, __GetDefaultStop(count, step)))

# Both bounds are reversed: the -1 stop sentinel becomes count, which is the exclusive stop the reversed view expects.
def __AsReversedKey(start: int, stop: int, step: int, count: int) -> slice:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, count)

    return slice(reverseIndex(start), reverseIndex(stop), -step)

def SetValues[T](lst: IListBase[T], key: slice, values: Iterable[T]|ICountableEnumerable[T]) -> None:
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

    count: int = lst.GetCount()

    i, l = __ResolveBounds(key, count, s)

    if s < 0: SetValues(lst.AsReversed(), __AsReversedKey(i, l, s, count), values)

    elif s == 1:
        if i > l: raise IndexError()

        length: int = l - i

        if length > 0: lst.RemoveRange(i, length)

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
    s: int|None = key.step

    if s is None: s = 1
    elif s == 0: raise IndexError()

    count: int = lst.GetCount()

    if count == 0: return

    i, l = __ResolveBounds(key, count, s)

    if s < 0:
        RemoveValues(lst.AsReversed(), __AsReversedKey(i, l, s, count))

        return

    if i >= l or i >= count or l == 0: return

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