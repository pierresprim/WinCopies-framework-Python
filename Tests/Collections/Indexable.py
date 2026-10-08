"""
Unit tests for indexable collections (WinCopies.Collections.Abstraction.Collection).

These tests use CPython's own list as the oracle: for every operation they
compare the framework's result against the same operation applied to a plain
list. Expected values are therefore never spelled out by hand, which keeps the
suite honest about slice and index semantics as it grows.
"""

import unittest
from collections.abc import Iterable, Sequence, MutableSequence
from typing import Callable

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import CreateList, CreateSizedList
from WinCopies.Collections.Extensions import ITuple, IList
from WinCopies.Collections.Iteration import Select
from WinCopies.Collections.Range import SetValues
from WinCopies.Collections.Util import MakeSequence, CreateSequence, CreateTuple, CreateList as CreatePyList
from WinCopies.String import StringifyIfNone

_SOURCE: Sequence[int] = (0, 1, 2, 3, 4)

def _create(items: ReadOnlyArray[int]|None = None) -> IList[int]:
    return CreateList(_SOURCE if items is None else items)

def _dump[T](items: ITuple[T]) -> ReadOnlyArray[T]:
    return CreateTuple(Select(range(items.GetCount()), items.GetAt))

def _format(key: slice) -> str:
    step: int|None = key.step

    return f"[{StringifyIfNone(key.start)}:{StringifyIfNone(key.stop)}{StringifyIfNone(step, ':')}]"

def _GetSlices(*values: tuple[int|None, int|None]|tuple[int|None, int|None, int|None]) -> Sequence[slice]:
    return CreateSequence(Select(values, lambda value: slice(*value)))
def _GetSliceTuples(*values: tuple[tuple[int|None, int|None]|tuple[int|None, int|None, int|None], Sequence[int]]) -> Sequence[tuple[slice, Sequence[int]]]:
    return CreateSequence(Select(values, lambda value: (slice(*(value[0])), value[1])))

def _Iterate() -> Iterable[int]:
    return range(len(_SOURCE))

def _AssertEqual(testCase: unittest.TestCase, actual: ReadOnlyArray[int], expected: Sequence[int]) -> None:
    testCase.assertEqual(len(actual), len(expected))

    for _actual, _expected in zip(actual, expected): testCase.assertEqual(_actual, _expected)

_KEYS: Sequence[slice] = _GetSlices(
    (1, 3), (0, 2), (2, 5), (0, 5), (None, None),
    (3, 1), (2, 2), (10, 20),
    (0, 5, 2), (1, None, 2), (None, None, 3),
    (4, 1, -1), (4, 0, -2), (4, None, -1), (None, 1, -1),
    (None, None, -1), (None, None, -2), (None, None, -3), (1, 4, -1),
    (4, -1, -1), (None, -1), (-3, None), (-4, -1), (-1, None),
    (-2, -1), (None, -6), (-6, None), (-1, -1), (-5, None),
    # D-64. A bound past either end resolved to itself, where slice.indices clamps it, so the
    # slice deleted was not the slice asked for: [5:1:-1] was measured to delete nothing
    # against CPython's (0, 1), and [None:7:-1] to delete all but the first against CPython's
    # nothing at all. (10, 20) above reaches none of this -- RemoveValues clamps its own stop
    # to the count on the resizable path -- so an out-of-range bound needs a step to show.
    (5, 1, -1), (5, None, -1), (7, None, -1), (None, 7, -1), (7, 5, -1),
    (7, 2, -2), (None, 6, -2), (6, None, -3), (-9, 7, 1), (None, 7, 2))

class TestReversedView(unittest.TestCase):
    """A reversed view must satisfy reversed[k] == source[n - 1 - k] on every path."""

    def test_indexing_mirrors_the_source(self) -> None:
        collection: IList[int] = _create()
        reversed_: ITuple[int] = collection.AsReversed()
        count: int = collection.GetCount()

        for i in range(count):
            with self.subTest(index = i):
                self.assertEqual(reversed_.GetAt(i), collection.GetAt(count - 1 - i))

    def test_enumeration_yields_the_reversed_source(self) -> None:
        self.assertEqual(_dump(_create().AsReversed()), CreateSequence(reversed(_SOURCE)))

    def test_midpoint_is_a_fixed_point(self) -> None:
        """The middle index maps to itself, so it is the cheapest tell that the mapping is sound."""

        collection: IList[int] = _create()

        self.assertEqual(collection.AsReversed().GetAt(2), collection.GetAt(2))

    def __assertInserted(self, count: int, action: Callable[[IList[int], int], None], expected: Callable[[MutableSequence[int], int], None]) -> None:
        for size in (0, 1, 3, 5):
            source: ReadOnlyArray[int] = CreateTuple(range(size))

            for index in range(size + 1):
                with self.subTest(size = size, index = index, count = count):
                    collection: IList[int] = _create(source)

                    action(collection.AsReversed(), index)

                    reference: MutableSequence[int] = CreatePyList(reversed(source))

                    expected(reference, index)

                    self.assertEqual(_dump(collection), CreateTuple(reversed(reference)))

    def test_try_insert_at_every_position(self) -> None:
        def insert(reference: MutableSequence[int], index: int) -> None: reference.insert(index, 99)

        self.__assertInserted(1, lambda items, index: self.assertTrue(items.TryInsert(index, 99)), insert)

    def test_insert_at_every_position(self) -> None:
        def insert(reference: MutableSequence[int], index: int) -> None: reference.insert(index, 99)

        self.__assertInserted(1, lambda items, index: items.AsMutableSequence().insert(index, 99), insert)

    def test_try_insert_range_at_every_position(self) -> None:
        """A single item hides a double reversal, so the range must carry several."""

        def check(values: Sequence[int]) -> None:
            def action(items: IList[int], index: int) -> None: items.TryInsertRange(index, CreatePyList(values))
            def insert(reference: MutableSequence[int], index: int) -> None: reference[index:index] = values

            self.__assertInserted(len(values), action, insert)
        def makeSequence(*values: ReadOnlyArray[int]) -> Sequence[ReadOnlyArray[int]]: return values

        for values in makeSequence((7, 8, 9), (9,), MakeSequence()): check(values)

    def test_add_appends_to_the_reversed_tail(self) -> None:
        collection: IList[int] = _create((0, 1, 2))

        collection.AsReversed().Add(99)

        self.assertEqual(_dump(collection), (99, 0, 1, 2))

    def test_add_range_appends_to_the_reversed_tail(self) -> None:
        collection: IList[int] = _create((0, 1, 2))

        collection.AsReversed().AddRange((7, 8, 9))

        self.assertEqual(_dump(collection), (9, 8, 7, 0, 1, 2))

    def test_removal_mirrors_the_source(self) -> None:
        for index in _Iterate():
            with self.subTest(index = index):
                collection: IList[int] = _create()

                self.assertTrue(collection.AsReversed().TryRemoveAt(index))

                reference: MutableSequence[int] = CreatePyList(reversed(_SOURCE))

                del reference[index]

                _AssertEqual(self, _dump(collection), CreateSequence(reversed(reference)))

class TestRemoveRange(unittest.TestCase):
    """TryRemoveRange must report what it did, and do exactly what it reports."""

    def test_valid_ranges_remove_and_report_true(self) -> None:
        for index in _Iterate():
            for count in range(1, len(_SOURCE) - index + 1):
                with self.subTest(index = index, count = count):
                    collection: IList[int] = _create()

                    self.assertTrue(collection.TryRemoveRange(index, count))

                    reference: MutableSequence[int] = CreatePyList(_SOURCE)

                    del reference[index:index + count]

                    _AssertEqual(self, _dump(collection), reference)

    def test_a_none_count_removes_to_the_end(self) -> None:
        for index in _Iterate():
            with self.subTest(index = index):
                collection: IList[int] = _create()

                self.assertTrue(collection.TryRemoveRange(index, None))
                self.assertEqual(_dump(collection), _SOURCE[:index])

    def test_rejected_ranges_report_false_and_change_nothing(self) -> None:
        for index, count in ((0, 0), (2, 0), (0, 99), (2, 4), (4, 2), (5, 1), (-1, 2)):
            with self.subTest(index = index, count = count):
                collection: IList[int] = _create()

                self.assertFalse(collection.TryRemoveRange(index, count))
                self.assertEqual(_dump(collection), _SOURCE)

class TestSliceSemantics(unittest.TestCase):
    """Slice deletion and assignment must agree with CPython on every form."""

    def test_deletion_matches_python(self) -> None:
        for key in _KEYS:
            with self.subTest(key = _format(key)):
                collection: IList[int] = _create()

                del collection.AsMutableSequence()[key]

                reference: MutableSequence[int] = CreatePyList(_SOURCE)

                del reference[key]

                _AssertEqual(self, _dump(collection), reference)

    def test_assignment_matches_python(self) -> None:
        cases: Sequence[tuple[slice, Sequence[int]]] = _GetSliceTuples(
            ((1, 3), (9, 9)), ((1, 3), (7, 8, 9)), ((1, 3), ()),
            ((0, 5), ()), ((2, 2), (9,)),
            ((0, 5, 2), (7, 8, 9)), ((None, None, 2), (7, 8, 9)),
            ((4, 1, -1), (7, 8, 9)), ((None, 1, -1), (7, 8, 9)),
            ((None, None, -1), (5, 6, 7, 8, 9)), ((4, None, -1), (5, 6, 7, 8, 9)),
            ((4, 0, -2), (7, 8)), ((None, None, -2), (7, 8, 9)),
            # D-64, on the keys CPython accepts: a start or a stop past an end, which
            # resolved to itself and addressed a slice the caller never asked for. Measured
            # before the clamp: [7:2:-1] = (7, 8) left (0, 1, 2, 8, 7, 3, 4), two items longer
            # than the list it was given, and [7:1:-3] = (7,) wrote at index 2 where CPython
            # writes at 4.
            ((7, 2, -1), (7, 8)), ((5, None, -1), (7, 8, 9, 10, 11)),
            ((4, 7, -1), ()), ((7, 1, -3), (7,)),
            ((-6, 7, 1), (7, 8)), ((None, 7), (9,)), ((9, None), (9,)),
            ((-3, None), (9,)), ((None, -1), (9,)))

        for key, values in cases:
            with self.subTest(key = _format(key), values = values):
                collection: IList[int] = _create()

                SetValues(collection, key, CreatePyList(values))

                reference: MutableSequence[int] = CreatePyList(_SOURCE)
                reference[key] = values

                _AssertEqual(self, _dump(collection), reference)

    def test_assignment_refuses_what_python_refuses(self) -> None:
        """D-61. The oracle's other half: the sizes CPython will not take.

        test_assignment_matches_python compares two contents, so it can only carry keys
        CPython accepts -- and every negative-step row it held happened to be exact-size,
        which is how D-61 passed through it. CPython treats every step but 1 as an extended
        slice, whose assignment must be exactly the slice's length. A step of -1 reversed into
        the resizable step of 1 and resized the list instead: measured on (0, 1, 2, 3, 4),
        [::-1] = (7, 8) left (8, 7), [4:1:-1] = () left (0, 1), and [4:-1:-1] = (7, 8, 9)
        left eight elements where it found five.

        The oracle is asserted first on every row, so that a row which stops being a refusal
        in CPython reads as this bench needing rewriting rather than as the framework passing.
        """

        cases: Sequence[tuple[slice, Sequence[int]]] = _GetSliceTuples(
            # Step -1, which is where the divergence was: short, long, and empty against a
            # non-empty slice. The last two keys resolve to an empty slice, so any assignment
            # at all is one item too many.
            ((None, None, -1), (7, 8)), ((4, 1, -1), (7, 8)),
            ((4, 1, -1), (1, 2, 3, 4)), ((4, 1, -1), ()), ((None, None, -1), ()),
            ((1, 4, -1), (7,)), ((4, -1, -1), (7, 8, 9)),
            # A bound past an end, which is D-64's ground: the rule has to be applied to the
            # clamped length, or it refuses by a length no slice ever had.
            ((None, 9, -1), (7, 8, 9, 10, 11)), ((9, None, -1), (7, 8)),
            # The steps that already refused, so that the one rule is seen to hold for all of
            # them rather than only for the step it was added at.
            ((None, None, -2), (7, 8)), ((None, None, -3), (7, 8, 9, 9)),
            ((None, None, 2), (7, 8)), ((0, 5, 2), (7, 8)))

        for key, values in cases:
            with self.subTest(key = _format(key), values = values):
                reference: MutableSequence[int] = CreatePyList(_SOURCE)

                with self.assertRaises(ValueError, msg = "CPython accepts this: the row, not the framework, is wrong"):
                    reference[key] = values

                collection: IList[int] = _create()

                with self.assertRaises(ValueError): SetValues(collection, key, CreatePyList(values))

                # A refusal that had already written part of the slice would satisfy the raise
                # above, which is half of what D-61 did on the resizable branch.
                _AssertEqual(self, _dump(collection), _SOURCE)

    def test_assignment_accepts_a_single_pass_iterable(self) -> None:
        collection: IList[int] = _create()

        SetValues(collection, slice(1, 3), (value for value in (9, 9)))

        reference: MutableSequence[int] = CreatePyList(_SOURCE)
        reference[1:3] = [9, 9]

        _AssertEqual(self, _dump(collection), reference)

    def test_a_stepped_slice_accepts_a_single_pass_iterable(self) -> None:
        """Every stepped slice measures the values before writing, and measuring a one-pass
        iterable consumes it.

        The case above covers the step of 1, which resizes and never counts. A step that
        counts went through a queue whose GetCount() was measured at 0 before the iterable is
        drained, so every one of these raised "a sequence of size 0" against a slice that
        wanted three. The negative steps carry the second half of the same seam: the count is
        taken before the reversal, so what the reversal receives has to be the counted items
        and not the caller's exhausted iterable.
        """

        cases: Sequence[tuple[slice, Sequence[int]]] = _GetSliceTuples(
            ((0, 5, 2), (7, 8, 9)), ((None, None, 2), (7, 8, 9)),
            ((4, 1, -1), (7, 8, 9)), ((None, None, -1), (5, 6, 7, 8, 9)),
            ((4, 0, -2), (7, 8)), ((None, None, -2), (7, 8, 9)))

        for key, values in cases:
            with self.subTest(key = _format(key), values = values):
                collection: IList[int] = _create()

                SetValues(collection, key, (value for value in values))

                reference: MutableSequence[int] = CreatePyList(_SOURCE)
                reference[key] = values

                _AssertEqual(self, _dump(collection), reference)

class TestTryMembersDoNotRaise(unittest.TestCase):
    """A Try* member reports a refusal; only its throwing counterpart raises."""

    def __createFull(self) -> IList[int]:
        return CreateSizedList([0, 1, 2])

    def test_try_insert_refuses_at_every_bound(self) -> None:
        for index in (0, 3):
            with self.subTest(index = index):
                collection: IList[int] = self.__createFull()

                self.assertIsNot(collection.AsReversed().TryInsert(index, 9), True)
                self.assertEqual(_dump(collection), (0, 1, 2))

    def test_try_insert_range_refuses_at_every_bound(self) -> None:
        for index in (0, 3):
            with self.subTest(index = index):
                collection: IList[int] = self.__createFull()

                self.assertIsNot(collection.AsReversed().TryInsertRange(index, [9]), True)
                self.assertEqual(_dump(collection), (0, 1, 2))

class TestEmptyRange(unittest.TestCase):
    """Inserting nothing is a trivial success, not a failure."""

    def test_insert_range_accepts_an_empty_range(self) -> None:
        collection: IList[int] = _create()

        collection.InsertRange(0, [])

        self.assertEqual(_dump(collection), _SOURCE)

    def test_insert_values_accepts_no_value(self) -> None:
        collection: IList[int] = _create()

        collection.InsertValues(0)

        self.assertEqual(_dump(collection), _SOURCE)

if __name__ == "__main__": unittest.main()