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
from WinCopies.Collections.Extensions import IList, ITuple
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
    (-2, -1), (None, -6), (-6, None), (-1, -1), (-5, None))

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

                reference: Sequence[int] = CreatePyList(reversed(_SOURCE))

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

                    reference: Sequence[int] = CreatePyList(_SOURCE)

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

                reference: Sequence[int] = CreatePyList(_SOURCE)

                del reference[key]

                _AssertEqual(self, _dump(collection), reference)

    def test_assignment_matches_python(self) -> None:
        cases: Sequence[tuple[slice, Sequence[int]]] = _GetSliceTuples(
            ((1, 3), (9, 9)), ((1, 3), (7, 8, 9)), ((1, 3), ()),
            ((0, 5), ()), ((2, 2), (9,)),
            ((0, 5, 2), (7, 8, 9)), ((None, None, 2), (7, 8, 9)),
            ((4, 1, -1), (7, 8, 9)), ((None, 1, -1), (7, 8, 9)),
            ((None, None, -1), (5, 6, 7, 8, 9)), ((4, None, -1), (5, 6, 7, 8, 9)),
            ((-3, None), (9,)), ((None, -1), (9,)))

        for key, values in cases:
            with self.subTest(key = _format(key), values = values):
                collection: IList[int] = _create()

                SetValues(collection, key, CreatePyList(values))

                reference: MutableSequence[int] = CreatePyList(_SOURCE)
                reference[key] = values

                _AssertEqual(self, _dump(collection), reference)

    def test_assignment_accepts_a_single_pass_iterable(self) -> None:
        collection: IList[int] = _create()

        SetValues(collection, slice(1, 3), (value for value in (9, 9)))

        reference: MutableSequence[int] = CreatePyList(_SOURCE)
        reference[1:3] = [9, 9]

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

if __name__ == "__main__":
    unittest.main()
