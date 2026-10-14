from collections.abc import Container, Iterable
from typing import SupportsIndex, overload

from WinCopies.Collections.Abstraction.Mapping import Set
from WinCopies.Collections.Core import IList as IListBase, ISet
from WinCopies.Collections.Enumeration.Core import ICountableEnumerable, CreateCountableIterable
from WinCopies.Collections.Extensions import IList
from WinCopies.Collections.Iteration.Extensions import Count
from WinCopies.Collections.Range import ResolveKey
from WinCopies.Collections.Util import ReverseIndex, MakeSequence, GetSequenceIndex, ThrowIndexError, ThrowSliceLengthError, ThrowSpanRefusedError, ThrowDuplicateItemError, ThrowRepeatedItemError
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
    def _count() -> tuple[ICountableEnumerable[T], Iterable[T], int]:
        def asEnumerable() -> tuple[ICountableEnumerable[T], Iterable[T]]:
            return (items, items.AsIterable()) if isinstance(items, ICountableEnumerable) else (CreateCountableIterable(items), items)
        
        items, length = Count(values)

        return *asEnumerable(), length

    def getRange(start: int, stop: int, step: int) -> range:
        if step == 1: return range(start, max(start, stop))
        
        indices: range = range(start, stop, step)

        if len(indices) == _length: return indices
        
        ThrowSliceLengthError(_length, len(indices))
    def reverseIndex(index: int) -> int:
        return ReverseIndex(index, count)

    # Shared with SetValues rather than resolved here. This function used to take `start or 0`
    # and `stop or count`, which normalises no negative index and clamps no bound, so the two
    # decomposers of a span disagreed on 3074 keys of a 4704-key grid -- and 84 of those were
    # accepted and written wrong without raising, a negative stop resolving to an empty span
    # so that nothing was removed and everything was inserted. Range.ResolveKey says the rest.
    # Materialize to guarantee reiterability, and before the branch below rather than after
    # it: the length of the range is now needed on this side of the reversal.
    newItems, items, _length = _count()

    step, start, stop, count = ResolveKey(lst, key)

    if step < 0:
        # The extended-slice length, applied before the reversal, which hands the call to a
        # branch that no longer knows the step was negative: a step of -1 reverses into the
        # resizable step of 1, and that branch resized instead of refusing -- [::-1] = () was
        # measured to empty the collection where CPython raises. getRange already states the
        # rule; its range is discarded, the reversed call recomputing the span in its own
        # direction. This is the clause the generic primitive applies at the same place.
        getRange(start, stop, step)

        # The formula of Range.__AsReversedKey, applied to the resolved bounds: the stop
        # sentinel of -1 that a negative step resolves to becomes the count, which is the
        # exclusive stop the reversed view expects.
        SetOrderedValues(lst.AsReversed(), s, slice(reverseIndex(start), reverseIndex(stop), -step), items)

        return

    # Affected indices + size constraint
    indices: range = getRange(start, stop, step)

    # Phase 1 — Validation only
    oldSet: set[T] = set[T]()

    for idx in indices: oldSet.add(lst.GetAt(idx))

    seen: ISet[T] = Set[T]()

    # Two causes, so two messages: one refusal that cannot say which of the two it is would
    # be no better than no message at all.
    for item in items:
        if not seen.TryAdd(item): ThrowRepeatedItemError(item)
        if __Conflicts(s, item, oldSet): ThrowDuplicateItemError(item)

    # The container's own answer, which this phase cannot stand in for: the two loops above
    # validate the set's invariant, and a list that refuses for a reason of its own -- a fixed
    # capacity -- would still be met by Phase 2, once the removal has freed the positions.
    # Measured at SetOrderedValues(CreateSizedList(4, [0, 1, 2, 3]), ..., slice(1, 3),
    # (7, 8, 9)), which left [0, 3]. Asked last, so that the two causes above win whenever both
    # refusals apply; asked to raise, so that the container says its own, the error here only
    # guarding against an implementation answering False instead.
    if not lst.CanSetRange(CreateCountableIterable(indices), newItems, True): ThrowSpanRefusedError(_length, indices)

    # Phase 2 — Mutation (only if validation is entirely successful)
    for idx in indices: s.remove(lst.GetAt(idx))

    if step == 1:
        # Named for the span rather than for the collection: the count of the whole now comes
        # back from the shared resolution, under that name.
        length: int = len(indices)

        if length > 0: lst.RemoveRange(start, length)

        lst.InsertRange(start, items)
    
    else:
        j: int = start

        for item in items:
            lst.SetAt(j, item)

            j += step

    s.update(items)

def TrySetOrderedValue[T: HashableProtocol](lst: IListBase[T], s: set[T], index: int, value: T) -> bool|None:
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
def SetOrderedValue[T: HashableProtocol](lst: IListBase[T], s: set[T], index: int, value: T) -> None:
    match TrySetOrderedValue(lst, s, index, value):
        case None: ThrowIndexError(index)
        case False: ThrowDuplicateItemError(value)

        case _: pass

@overload
def SetOrderedItems[T: HashableProtocol](lst: IListBase[T], s: set[T], index: SupportsIndex, value: T) -> None:
    ...
@overload
def SetOrderedItems[T: HashableProtocol](lst: IListBase[T], s: set[T], index: slice, value: Iterable[T]) -> None:
    ...

def SetOrderedItems[T: HashableProtocol](lst: IListBase[T], s: set[T], index: SupportsIndex|slice, value: T|Iterable[T]) -> None:
    if isinstance(index, SupportsIndex): SetOrderedValue(lst, s, GetSequenceIndex(index, lst.GetCount()), value) # type: ignore
    else: SetOrderedValues(lst, s, index, value) # type: ignore