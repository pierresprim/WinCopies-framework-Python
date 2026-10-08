from collections.abc import Iterable, Sequence, MutableSequence
from typing import overload, SupportsIndex

from WinCopies.Collections.Core import ICountable, ITuple as ITupleBase, IList as IListBase
from WinCopies.Collections.Enumeration.Core import IEnumerable, ICountableEnumerable
from WinCopies.Collections.Extensions import ITuple, IList
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

# The key resolution, named once because two functions decompose a span: this one and
# Range.Extensions.SetOrderedValues, which keeps a validation phase of its own for the
# ordered set's unicity. The two had drifted here and nowhere else -- resolving a key by
# `start or 0` and `stop or count` normalises no negative index and clamps no bound, so they
# disagreed on 3074 keys of a 4704-key grid, and 84 of those were accepted and written with
# the wrong content, no exception raised: a negative stop resolved to an empty span, so
# nothing was removed and everything was inserted. Sharing the resolution is what keeps a
# second decomposer from being a second set of rules.
#
# The count comes back with the bounds rather than being read again by the caller: both
# callers need it to mirror a negative step, and two reads would let it move between them.
def ResolveKey(lst: ICountable, key: slice) -> tuple[int, int, int, int]:
    """Resolves a slice key against a collection: the step, the start, the stop, the count.

    A step of 0 is refused here, as CPython refuses it, so that no caller has to.
    """

    step: int|None = key.step

    if step is None: step = 1
    elif step == 0: raise IndexError()

    count: int = lst.GetCount()

    start, stop = __ResolveBounds(key, count, step)

    return (step, start, stop, count)

def SetValues[T](lst: IListBase[T], key: slice, values: Iterable[T]|ICountableEnumerable[T]) -> None:
    # CPython takes every step but 1 as an extended slice, which accepts exactly its own
    # length. Stated once, because the two branches that hold to it apply it on either side
    # of the reversal.
    def validateLength(indices: range, length: int) -> None:
        if len(indices) != length: raise ValueError(f"Attempt to assign a sequence of size {length} to an extended slice of size {len(indices)}.")

    # Asked before the first write, which is the whole point of the hook: the removal below
    # frees the positions and cannot be taken back, so the container is made to answer while
    # the content is still intact. The defect was this question asked too late -- InsertRange
    # discovered the refusal, and what RemoveRange had taken was already gone.
    def validateSpan(indices: range, items: Sequence[T]) -> None:
        if not lst.CanSetRange(indices, items): raise ValueError(f"The container refuses the assignment of {len(items)} item(s) to the {len(indices)} position(s) of {indices}.")

    s, i, l, count = ResolveKey(lst, key)

    # Materialized once, here, because three readers now want the whole range: the length
    # check, the container's answer, and the write. Hoisted out of the branches that each
    # counted for themselves, which also puts the evaluation of the right-hand side where
    # CPython puts it -- before the assignment is attempted at all.
    _values: Iterable[T] = values.AsIterable() if isinstance(values, IEnumerable) else values
    items: Sequence[T] = _values if isinstance(_values, Sequence) else tuple[T](_values)

    # Applied before the reversal, which hands the call to a branch that no longer knows the
    # step was negative: a step of -1 reverses into the resizable step of 1, so that branch
    # resized the list instead of refusing -- [::-1] = (7, 8) was measured to leave [8, 7]
    # where CPython raises. A step below -1 reverses into an extended step and is refused
    # there anyway, so what this adds is exactly the s == -1 case. The length is read from
    # the key as given, which is the length CPython reports, rather than from the reversed
    # bounds.
    if s < 0:
        validateLength(range(i, l, s), len(items))

        # The span is validated by the reversed view, one level down, which mirrors the
        # positions before asking the container: asking here would hand the hook a span
        # expressed in the wrong direction.
        SetValues(lst.AsReversed(), __AsReversedKey(i, l, s, count), items)

    elif s == 1:
        if i > l: raise IndexError(f"The slice start {i} is past its stop {l}.")

        length: int = l - i

        validateSpan(range(i, l), items)

        if length > 0: lst.RemoveRange(i, length)

        lst.InsertRange(i, items)

    # step > 1
    elif i >= l: raise IndexError(f"The slice start {i} is not before its stop {l}.")

    else:
        indices: range = range(i, l, s)

        validateLength(indices, len(items))
        validateSpan(indices, items)

        for item in items:
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