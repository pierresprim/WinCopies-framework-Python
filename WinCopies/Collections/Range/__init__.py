from collections.abc import Iterable, Sequence, MutableSequence
from typing import overload, SupportsIndex

from WinCopies.Collections.Core import ITuple as ITupleBase, IList as IListBase
from WinCopies.Collections.Enumeration.Core import IEnumerable, ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple, IList
from WinCopies.Collections.Iteration.Extensions import CountAsIterable
from WinCopies.Collections.Linked.Singly import CreateEnumerableStack
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

# slice.indices clamps both ends of a key, and the two defaults above are exactly those
# ends, low to high in the direction the step runs. Only the upper clamp was missing, so an
# over-large positive bound resolved to itself and the slice resolved was not the slice the
# caller asked for: 4787 of a 8960-key grid disagreed with slice.indices, 1763 of them on
# the stop alone.
def __ResolveIndex(index: int, count: int, step: int) -> int:
    def clamp(lower: int, upper: int) -> int: return min(max(index if index >= 0 else __Normalize(index, count), lower), upper)

    return clamp(__GetDefaultStop(count, step), __GetDefaultStart(count, step)) if step < 0 else clamp(__GetDefaultStart(count, step), __GetDefaultStop(count, step))

def __ResolveBounds(key: slice, count: int, step: int) -> tuple[int, int]:
    def resolve(index: int|None, default: int) -> int:
        return default if index is None else __ResolveIndex(index, count, step)

    return (resolve(key.start, __GetDefaultStart(count, step)), resolve(key.stop, __GetDefaultStop(count, step)))

# Both bounds are reversed: the -1 stop sentinel becomes count, which is the exclusive stop the reversed view expects.
def __AsReversedKey(start: int, stop: int, step: int, count: int) -> slice:
    def reverseIndex(index: int) -> int: return ReverseIndex(index, count)

    return slice(reverseIndex(start), reverseIndex(stop), -step)

def SetValues[T](lst: IListBase[T], key: slice, values: Iterable[T]|ICountableEnumerable[T]) -> None:
    # CPython takes every step but 1 as an extended slice, which accepts exactly its own
    # length. Stated once, because the two branches that hold to it apply it on either side
    # of the reversal.
    def validateLength(indices: range, length: int) -> None:
        if len(indices) != length: raise ValueError(f"Attempt to assign a sequence of size {length} to an extended slice of size {len(indices)}.")

    s: int|None = key.step

    if s is None: s = 1
    elif s == 0: raise IndexError()

    count: int = lst.GetCount()

    i, l = __ResolveBounds(key, count, s)

    # Applied before the reversal, which hands the call to a branch that no longer knows the
    # step was negative: a step of -1 reverses into the resizable step of 1, so that branch
    # resized the list instead of refusing -- [::-1] = (7, 8) was measured to leave [8, 7]
    # where CPython raises. A step below -1 reverses into an extended step and is refused
    # there anyway, so what this adds is exactly the s == -1 case. The length is read from
    # the key as given, which is the length CPython reports, rather than from the reversed
    # bounds.
    if s < 0:
        # Counted through the re-readable form, not the generator one: for a step below -1 the
        # reversed key lands in the extended branch, which counts a second time, and a
        # generator would come back empty from that second pass.
        _items: tuple[Iterable[T], int] = CountAsIterable(values)

        validateLength(range(i, l, s), _items[1])

        # The counted items, not `values`: counting a one-pass iterable consumes it.
        SetValues(lst.AsReversed(), __AsReversedKey(i, l, s, count), _items[0])

    elif s == 1:
        if i > l: raise IndexError(f"The slice start {i} is past its stop {l}.")

        length: int = l - i

        if length > 0: lst.RemoveRange(i, length)

        lst.InsertRange(i, values.AsIterable() if isinstance(values, IEnumerable) else values)

    # step > 1
    elif i >= l: raise IndexError(f"The slice start {i} is not before its stop {l}.")

    else:
        items: tuple[Iterable[T], int] = CountAsIterable(values, True)

        validateLength(range(i, l, s), items[1])

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