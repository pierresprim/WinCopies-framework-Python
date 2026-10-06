from collections.abc import Container, Iterable, Sequence
from typing import SupportsIndex, overload

from WinCopies.Collections.Abstraction.Mapping import Set
from WinCopies.Collections.Core import IList, ISet
from WinCopies.Collections.Util import ReverseIndex, MakeSequence
from WinCopies.Typing.Comparison import HashableProtocol

def __Conflicts[T: HashableProtocol](s: set[T], value: T, leaving: Container[T]) -> bool:
    """Whether value collides with an element the set keeps.

    What `leaving` holds is what this write removes, so it is out of the unicity test: a
    position cannot conflict with the value replacing the one it is about to give up. The
    scalar write hands it the single value at the index, the slice write the values at every
    index the slice covers.
    """

    return value in s and value not in leaving

def SetOrderedValues[T: HashableProtocol](lst: IList[T], s: set[T], key: slice, values: Iterable[T]) -> None:
    def reverseIndex(index: int) -> int:
        return ReverseIndex(index, lst.GetCount())

    step: int|None = key.step

    if step is None: step = 1
    elif step == 0: raise IndexError()

    start: int|None = key.start
    stop: int|None = key.stop

    if start is None: start = 0
    if stop is None: stop = lst.GetCount()

    if step < 0:
        SetOrderedValues(lst.AsReversed(), s, slice(reverseIndex(start), reverseIndex(stop), -step), values)

        return

    # Materialize to guarantee reiterability
    newItems: Sequence[T] = values if isinstance(values, Sequence) else tuple[T](values)

    # Affected indices + size constraint
    if step == 1: indices: range = range(start, max(start, stop))
    else:
        indices = range(start, stop, step)

        if len(indices) != len(newItems): raise ValueError()

    # Phase 1 — Validation only
    oldSet: set[T] = set[T]()

    for idx in indices: oldSet.add(lst.GetAt(idx))

    seen: ISet[T] = Set[T]()

    for item in newItems:
        if not seen.TryAdd(item) or __Conflicts(s, item, oldSet): raise ValueError()  # Internal duplicate of new items, OR conflict with an item the set keeps

    # Phase 2 — Mutation (only if validation is entirely successful)
    for idx in indices: s.remove(lst.GetAt(idx))

    if step == 1:
        count: int = len(indices)

        if count > 0: lst.RemoveRange(start, count)

        lst.InsertRange(start, newItems)
    
    else:
        j: int = start

        for item in newItems:
            lst.SetAt(j, item)

            j += step

    s.update(newItems)

def TrySetOrderedValue[T: HashableProtocol](lst: IList[T], s: set[T], index: int, value: T) -> bool|None:
    """Writes value at index, keeping s in step with lst.

    None: the index is refused. False: the value collides with one the set keeps, which the
    unicity of the ordered set forbids. True: written.
    """

    if not lst.ValidateIndex(index): return None

    old: T = lst.GetAt(index)

    # A one-tuple rather than a set: `leaving` holds one value here, so this is one equality
    # test instead of a hash and a lookup.
    if __Conflicts(s, value, MakeSequence(old)): return False

    # Both sides are replaced unconditionally, as the slice write does: the position holds
    # the value passed, and the set holds the very object the list holds.
    s.remove(old)
    s.add(value)

    lst.SetAt(index, value)

    return True
def SetOrderedValue[T: HashableProtocol](lst: IList[T], s: set[T], index: int, value: T) -> None:
    match TrySetOrderedValue(lst, s, index, value):
        # KeyError, not IndexError, because that is what IWriter.SetAt raises for a refused
        # index across every type: this write must not diverge from its siblings. Whether
        # KeyError is the right choice there at all is a question for IWriter, not for here.
        case None: raise KeyError(f"Key {index} does not exist.")
        case False: raise ValueError()

        case _: return None

@overload
def SetOrderedItems[T: HashableProtocol](lst: IList[T], s: set[T], index: SupportsIndex, value: T) -> None:
    ...
@overload
def SetOrderedItems[T: HashableProtocol](lst: IList[T], s: set[T], index: slice, value: Iterable[T]) -> None:
    ...

def SetOrderedItems[T: HashableProtocol](lst: IList[T], s: set[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex): SetOrderedValue(lst, s, int(index), value) # type: ignore
    else: SetOrderedValues(lst, s, index, value) # type: ignore