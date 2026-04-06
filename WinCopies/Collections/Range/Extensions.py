from collections.abc import Iterable, Sequence
from typing import SupportsIndex, overload

from WinCopies.Collections import IList, ISet, ReverseIndex
from WinCopies.Collections.Abstraction.Collection.Mapping import Set
from WinCopies.Typing import IEquatableItem

def SetOrderedValues[T: IEquatableItem](lst: IList[T], s: set[T], key: slice, values: Iterable[T]) -> None:
    def reverseIndex(index: int) -> int:
        return ReverseIndex(index, lst.GetCount())

    step: int|None = key.step

    if step is None:
        step = 1
    elif step == 0:
        raise IndexError()

    start: int|None = key.start
    stop: int|None = key.stop

    if start is None:
        start = 0
    if stop is None:
        stop = lst.GetCount()

    if step < 0:
        SetOrderedValues(lst.AsReversed(), s, slice(reverseIndex(start), reverseIndex(stop), -step), values)

        return

    # Materialize to guarantee reiterability
    newItems: Sequence[T] = values if isinstance(values, Sequence) else tuple[T](values)

    # Affected indices + size constraint
    if step == 1:
        indices: range = range(start, max(start, stop))
    else:
        indices = range(start, stop, step)

        if len(indices) != len(newItems):
            raise ValueError()

    # Phase 1 — Validation only
    oldSet: set[T] = set[T]()

    for idx in indices:
        oldSet.add(lst.GetAt(idx))

    seen: ISet[T] = Set[T]()

    for item in newItems:
        if not seen.TryAdd(item) or (item in s and not item in oldSet):
            raise ValueError()  # Internal duplicate of new items OR Conflict with an existing item outside the slice

    # Phase 2 — Mutation (only if validation is entirely successful)
    for idx in indices:
        s.remove(lst.GetAt(idx))

    if step == 1:
        count: int = len(indices)

        if count > 0:
            lst.RemoveRange(start, count)

        lst.InsertRange(start, newItems)
    
    else:
        j: int = start

        for item in newItems:
            lst.SetAt(j, item)

            j += step

    s.update(newItems)

@overload
def SetOrderedItems[T: IEquatableItem](lst: IList[T], s: set[T], index: SupportsIndex, value: T) -> None:
    ...
@overload
def SetOrderedItems[T: IEquatableItem](lst: IList[T], s: set[T], index: slice, value: Iterable[T]) -> None:
    ...

def SetOrderedItems[T: IEquatableItem](lst: IList[T], s: set[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex):
        lst.SetAt(int(index), value) # type: ignore
    
    else:
        SetOrderedValues(lst, s, index, value) # type: ignore