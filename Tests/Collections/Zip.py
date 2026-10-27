"""
Benches for the equality of two sequences (WinCopies.Collections.Loop.AreEquals) and for the zip
it walks them with (WinCopies.Collections.Iteration.Enumeration: Zip, TryZip and IZipInfo).

AreEquals had no bench of its own. The suite reached it only through the equalities built on it,
the ordered set's tuples and AreTuplesEqual, and only ever with two tuples of the same three items:
never an empty sequence, never two of different lengths. That is where D-113 lived, in three places
at once (4.40 §4). Two empty sequences were unequal, because a walk that processed nothing answered
None, and None is not True. The zip drew one item too many from x before it found y exhausted, so
an x longer by one item compared equal. And the countable branch, having found two different
counts, went on to that zip instead of answering. Pierre's correction has the zip report which side
ran out, IZipInfo, and the report's first version was wrong in two ways of its own (4.41 §4).

So these benches put AreEquals to empty, unequal and reordered sequences, on each of the forms it
branches on, and read the zip's report on each outcome.
"""

import unittest

from collections.abc import Generator, Iterable, Iterator, Sequence
from typing import Any
from unittest import mock

import WinCopies.Collections.Abstraction.Mapping.Extensions as MappingExtensions
import WinCopies.Collections.Iteration.Enumeration as Enumeration
import WinCopies.Collections.Loop as Loop

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import EquatableTuple, List
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Enumeration.Core import IEnumerable, IEnumerator, ICountableEnumerable, AsIterable, AsEnumerable, AsEnumerator
from WinCopies.Collections.Extensions import IEquatableTuple
from WinCopies.Collections.Iteration import IncludeWhileTrue
from WinCopies.Collections.Iteration.Enumeration import IZipInfo
from WinCopies.Typing import INullable, InvalidOperationError, GetNullValue, GetNullable, GetNullableValue
from WinCopies.Typing.Delegate import Method, Converter
from WinCopies.Typing.Pairing import IKeyValuePair, CreateDualResult

type _Items = IEnumerable[int]|Iterable[int]
type _Form = Converter[ReadOnlyArray[int], _Items]

def _generate(items: ReadOnlyArray[int]) -> Generator[int]: yield from items

# The pairs AreEquals branches on. Two countable collections are compared by their counts first, a
# countable collection and a list by the count and the length, two lists by their lengths, and
# anything else, an iterator or a generator, by walking both to their ends. The countable pair is the
# one 4.40 §4 measured: List.AsImmutable() against an EquatableTuple, which is also a Sequence.
_PAIRS: ReadOnlyArray[tuple[str, _Form, _Form]] = (
    ("lists",                             lambda items: list(items),                   lambda items: list(items)),
    ("countable collections",             lambda items: List[int](items).AsImmutable(), lambda items: EquatableTuple[int](items)),
    ("a countable collection and a list", lambda items: List[int](items).AsImmutable(), lambda items: list(items)),
    ("iterators",                         lambda items: iter(items),                   lambda items: iter(items)),
    ("generators",                        _generate,                                   _generate))

class TestAreEqualsComparesBothSequencesToTheirEnds(unittest.TestCase):
    """D-113. AreEquals promised what the equality of the tuples promises (4.5, 4.10): the same items,
    in the same order, and nothing more on either side. It held only between two non-empty sequences
    of one length. Two empty ones were unequal, and an x longer than y by one item was equal to it.
    The second held on every pair, the countable ones included, since the countable branch fell
    through to the zip when the counts differed. Nothing measured it: the only benches that reached
    AreEquals compared two tuples of the same three items."""

    def __assertAnswers(self, x: ReadOnlyArray[int], y: ReadOnlyArray[int], expected: bool, what: str) -> None:
        for pair, makeX, makeY in _PAIRS:
            with self.subTest(pair = pair, x = x, y = y): self.assertIs(Loop.AreEquals(makeX(x), makeY(y)), expected, f"{what}: AreEquals answers otherwise on {pair}")

    def test_two_empty_sequences_are_equal(self) -> None: self.__assertAnswers((), (), True, "two empty sequences")

    def test_sequences_of_different_lengths_are_unequal(self) -> None:
        """A difference of one item, in both directions: it is the one the zip lost. A longer x lost
        its last item to the zip and compared equal; a longer y was found, since the zip stops on x
        before asking y again."""

        for x, y in (((1, 2), (1,)), ((1,), (1, 2))): self.__assertAnswers(x, y, False, f"{len(x)} items against {len(y)}")

    def test_sequences_compare_item_by_item_in_order(self) -> None:
        """The two answers the benches above rely on: a walk that answers at all, and one that reads
        the order. Neither of the benches above can fail on an equality that never answers True."""

        self.__assertAnswers((1, 2), (1, 2), True, "the same items in the same order")
        self.__assertAnswers((1, 2), (2, 1), False, "the same items in another order")

def _zip(x: _Items, y: _Items) -> tuple[ReadOnlyArray[tuple[int, int]], IZipInfo]:
    """Walks the zip to its end, and answers the pairs it gave and the report it handed over."""

    reports: list[IZipInfo] = []
    pairs: ReadOnlyArray[tuple[int, int]] = tuple((pair.GetKey(), pair.GetValue()) for pair in Enumeration.Zip(x, y, reports.append))

    (report,) = reports

    return (pairs, report)

# The outcomes of a zip, and what its report says of each: True when x is the longer, False when y
# is, None when neither is.
_OUTCOMES: ReadOnlyArray[tuple[str, ReadOnlyArray[int], ReadOnlyArray[int], bool|None]] = (
    ("x longer",      (1, 2), (1,),   True),
    ("y longer",      (1,),   (1, 2), False),
    ("equal lengths", (1, 2), (1, 2), None),
    ("both empty",    (),     (),     None))

class TestTheZipReportsTheLongerSide(unittest.TestCase):
    """D-113, the report the correction added. AreEquals reads it to tell a full match from a match
    of the shorter side alone, so a wrong report is a wrong equality. Its first version, at 06a00ff,
    was wrong twice: the end of the zip overwrote "x is longer" with "equal lengths", and "equal
    lengths", which is None, was not stored as a value, so a finished zip still read as a running
    one. Both are read here, as is the refusal that a running zip owes.

    The zip itself is asserted too. At d4c9197 it stopped on the first None that y gave, and TryZip
    answered an absent x with a zip; e69a028 changed both."""

    def test_the_report_names_the_longer_side(self) -> None:
        """On lists and on iterators: AreEquals hands the zip iterators, and the other benches here
        hand it lists."""

        forms: ReadOnlyArray[tuple[str, _Form]] = (("lists", lambda items: list(items)), ("iterators", lambda items: iter(items)))

        for form, make in forms:
            for outcome, x, y, expected in _OUTCOMES:
                with self.subTest(form = form, outcome = outcome):
                    pairs, report = _zip(make(x), make(y))

                    self.assertEqual(pairs, tuple(zip(x, y)), f"{outcome}: the zip gave other pairs")

                    try: answer: bool|None = report.GetValue()
                    except InvalidOperationError: self.fail(f"{outcome}: the report is still refused once the zip has ended")

                    self.assertIs(answer, expected, f"{outcome}: the report says {answer!r}")

    def test_the_report_is_refused_until_the_zip_has_ended(self) -> None:
        """The report is handed over before the zip runs, and before it has ended it has nothing to
        say: an answer then would be a guess."""

        reports: list[IZipInfo] = []
        pairs: Iterator[IKeyValuePair[int, int]] = Enumeration.Zip((1, 2), (1, 2), reports.append)

        (report,) = reports

        with self.subTest(moment = "before the first pair"): self.assertRaises(InvalidOperationError, report.GetValue)

        next(pairs)

        with self.subTest(moment = "after the first pair"): self.assertRaises(InvalidOperationError, report.GetValue)

        for _ in pairs: pass

        with self.subTest(moment = "once the zip has ended"): self.assertIsNone(report.GetValue())

    def test_the_zip_pairs_every_item_and_an_absent_side_gives_no_zip(self) -> None:
        with self.subTest(y = "(None, 5)"):
            self.assertEqual(tuple((pair.GetKey(), pair.GetValue()) for pair in Enumeration.Zip((1, 2, 3), (None, 5))), ((1, None), (2, 5)),
                             "the zip does not pair every item up to the end of the shorter side")

        for side, x, y in (("x", None, (1,)), ("y", (1,), None)):
            with self.subTest(absent = side): self.assertIsNone(Enumeration.TryZip(x, y), f"TryZip answers an absent {side} with a zip")

def _orderedSetTuple(*items: int) -> IEquatableTuple[int]: return CreateOrderedSet(items).AsTuple()

class TestTheOrderedSetTupleComparesWholeIterables(unittest.TestCase):
    """D-113, through the one caller that hands AreEquals Python iterators. The ordered set's tuples
    compare with any iterable, where an EquatableTuple compares with tuples only (a divergence 4.10
    §5 records without ruling on it), and they compare through AreEquals. So an iterator put to one
    of them walks the branch D-113 broke at e69a028 and again at 06a00ff: the empty tuple was unequal
    to every empty iterable, the tuple [1, 2] was equal to [1], and at 06a00ff comparing with an
    iterator raised. Should the two families be aligned one day, the True halves below are what
    will turn red, and the question will be the alignment, not D-113."""

    def test_an_iterable_is_equal_only_to_the_same_items_in_the_same_order(self) -> None:
        items: IEquatableTuple[int] = _orderedSetTuple(1, 2)

        for other, value, expected in (("iter([1, 2])",    iter([1, 2]),    True),
                                       ("iter([1])",       iter([1]),       False),
                                       ("iter([1, 2, 3])", iter([1, 2, 3]), False),
                                       ("iter([2, 1])",    iter([2, 1]),    False),
                                       ("[1]",             [1],             False)):
            with self.subTest(other = other): self.assertIs(items.Equals(value), expected, f"OrderedSet([1, 2]).AsTuple() against {other}")

    def test_the_empty_tuple_is_equal_to_every_empty_iterable(self) -> None:
        nothing: ReadOnlyArray[int] = ()
        empty: IEquatableTuple[int] = _orderedSetTuple()

        for other, value in (("iter([])", iter(nothing)), ("[]", list(nothing)), ("()", nothing), ("another empty tuple", _orderedSetTuple())):
            with self.subTest(other = other): self.assertTrue(empty.Equals(value), f"the empty tuple is not equal to {other}")

def _areEqualsAsAtE69a028[T1, T2](x: IEnumerable[T1]|Iterable[T1], y: IEnumerable[T2]|Iterable[T2]) -> bool:
    """AreEquals as it stood at e69a028, with the walk it went through then, ZipWhile over that day's
    zip. The countable branch fell through to the walk when the counts differed. The zip drew x's
    next item before it asked y for one, so the walk, which then checked that both sides were
    exhausted, found x exhausted when x was longer by one item: that item was already drawn."""

    def loop(x: IEnumerable[T1]|Iterable[T1], y: IEnumerable[T2]|Iterable[T2]) -> bool:
        def zip(y: IEnumerator[T2]) -> Generator[IKeyValuePair[T1, T2]]:
            for item in IncludeWhileTrue(AsIterable(x), y.MoveNext): yield CreateDualResult(item, y.GetCurrent())

        enumerator: IEnumerator[T2]|None = _enumeratorOf(y)

        return enumerator is not None and Loop.ForEachItem(zip(enumerator), lambda item: item.GetKey() == item.GetValue()) is True

    def equals(x: ICountableEnumerable[T1], y: Iterable[T2], yCount: int) -> bool: return x.GetCount() == yCount and loop(x, y)
    def sequenceEquals(x: ICountableEnumerable[T1], y: Sequence[T2]) -> bool: return equals(x, y, len(y))

    def iterableEquals(x: IEnumerable[T1]|Iterable[T1], y: IEnumerable[T2]|Iterable[T2]) -> bool:
        _x: IEnumerator[T1]|None = AsEnumerable(x).TryGetEnumerator()
        _y: IEnumerator[T2]|None = AsEnumerable(y).TryGetEnumerator()

        if _x is None: return _y is None
        if _y is None: return False

        return loop(_x.AsIterator(), _y.AsIterator()) and not (_x.MoveNext() or _y.MoveNext())

    return (x is y
            or (isinstance(x, ICountableEnumerable) and ((isinstance(y, ICountableEnumerable) and equals(x, y.AsIterable(), y.GetCount()))
                                                         or (isinstance(y, Sequence) and sequenceEquals(x, y))))
            or iterableEquals(x, y))

def _enumeratorOf(items: Iterable[Any]|IEnumerable[Any]) -> IEnumerator[Any]|None:
    """How TryZip has always obtained y's enumerator, unchanged by every commit rebuilt below."""

    match items:
        case Iterator(): return AsEnumerator(items)
        case Iterable(): return AsEnumerable(items).GetEnumerator()

        case IEnumerable(): return items.TryGetEnumerator()

class _RebuiltZipReport(IZipInfo):
    """The report as _ZipInfo stores it, or as it stored it at 06a00ff when `keepsNone` is False:
    through GetNullableValue, under which None is an absence of value and not a value."""

    def __init__(self, keepsNone: bool) -> None:
        super().__init__()

        self.__keepsNone: bool = keepsNone
        self.__value: INullable[bool|None] = GetNullValue()

    def TryGetValue(self) -> INullable[bool|None]: return self.__value

    def SetValue(self, value: bool|None) -> None: self.__value = GetNullable(value) if self.__keepsNone else GetNullableValue(value)

def _tryZipAsAt06a00ff(overwrites: bool, keepsNone: bool) -> Any:
    """TryZip with either cause of 4.41 §4, or neither: the loop left by `break`, so that the line
    after it ran too, and a report that does not keep None. _ZipInfo is private and no object hands
    it out, so TryZip, the public function that builds it and that Zip looks up, is what is
    replaced, with a report rebuilt beside it."""

    def tryZip(x: Iterable[Any]|IEnumerable[Any]|None, y: Iterable[Any]|IEnumerable[Any]|None, info: Method[IZipInfo]|None = None) -> Generator[IKeyValuePair[Any, Any]]|None:
        if x is None or y is None: return None

        items: Iterable[Any] = AsIterable(x)
        enumerator: IEnumerator[Any]|None = _enumeratorOf(y)
        report: _RebuiltZipReport = _RebuiltZipReport(keepsNone)

        if enumerator is None: return None

        def pairs(y: IEnumerator[Any]) -> Generator[IKeyValuePair[Any, Any]]:
            for item in items:
                if y.MoveNext(): yield CreateDualResult(item, y.GetCurrent())

                else:
                    report.SetValue(True)

                    if overwrites: break

                    return

            report.SetValue(False if y.MoveNext() else None)

        if info is not None: info(report)

        return pairs(enumerator)

    return tryZip

def _tryZipAsAtD4c9197(x: Iterable[Any]|IEnumerable[Any]|None, y: Iterable[Any]|IEnumerable[Any]|None, info: Method[IZipInfo]|None = None) -> Generator[IKeyValuePair[Any, Any]]|None:
    """TryZip as it stood at d4c9197, before e69a028 rewrote it: a None drawn from y ended the zip,
    and an absent x was answered with a zip instead of None. An absent y raised then, from an
    isinstance check outside TryZip, and that is not rebuilt. There was no report then; the
    parameter is taken because Zip, which looks TryZip up, now passes one."""

    items: Any = x.AsIterable() if isinstance(x, IEnumerable) else x

    def pairs(y: IEnumerator[Any]) -> Generator[IKeyValuePair[Any, Any]]:
        for item in items:
            if y.MoveNext():
                if (current := y.GetCurrent()) is None: break

                yield CreateDualResult(item, current)

            else: break

    enumerator: IEnumerator[Any]|None = None if y is None else _enumeratorOf(y)

    return None if enumerator is None else pairs(enumerator)

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheZipBenchesCanFail(unittest.TestCase):
    """The benches of D-113 and of the zip, run against the code as it stood before each correction:
    green on the intact tree, red on the rebuilt one. Each function is replaced where its callers
    look it up, and each cause is rebuilt alone, so that each is shown to be caught."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_empty_benches_fall_when_a_walk_over_nothing_answers_false(self) -> None:
        """As at e69a028: ZipWhile tested its walk with `is True`, and ForEachItem answers None when it
        processed nothing. Every AreEquals looks ZipWhile up in Loop, wherever it is called from. The
        rebuilt ZipWhile keeps today's signature, which hands the zip its report."""

        def zipWhile(x: Any, y: Any, predicate: Any, info: Any = None) -> Any: return Loop.ForEachItem(Enumeration.Zip(x, y, info), predicate) is True

        for bench, name in ((TestAreEqualsComparesBothSequencesToTheirEnds, "test_two_empty_sequences_are_equal"),
                            (TestTheOrderedSetTupleComparesWholeIterables, "test_the_empty_tuple_is_equal_to_every_empty_iterable")):
            with self.subTest(bench = name): self.__assertFalls(bench, name, Loop, {"ZipWhile": zipWhile})

    def test_the_length_benches_fall_when_the_longer_x_loses_its_last_item(self) -> None:
        """As at e69a028: AreEquals and the walk it went through then. It is replaced where it is looked
        up: in Loop for the benches that call it, and in the module of the ordered set's tuples, which
        imported it. Only an x longer by one item falls: a longer y was found, as it was then."""

        for bench, name, target in ((TestAreEqualsComparesBothSequencesToTheirEnds, "test_sequences_of_different_lengths_are_unequal", Loop),
                                    (TestTheOrderedSetTupleComparesWholeIterables, "test_an_iterable_is_equal_only_to_the_same_items_in_the_same_order", MappingExtensions)):
            with self.subTest(bench = name): self.__assertFalls(bench, name, target, {"AreEquals": _areEqualsAsAtE69a028})

    def test_the_report_benches_fall_when_the_end_of_the_zip_overwrites_the_report(self) -> None:
        """As at 06a00ff, the first cause of 4.41 §4: the zip left its loop by `break`, so the line
        after the loop ran as well and replaced "x is longer" with "equal lengths". AreEquals then took
        an x longer than y for an equal one, on the pairs that it walks."""

        for bench, name in ((TestTheZipReportsTheLongerSide, "test_the_report_names_the_longer_side"),
                            (TestAreEqualsComparesBothSequencesToTheirEnds, "test_sequences_of_different_lengths_are_unequal")):
            with self.subTest(bench = name): self.__assertFalls(bench, name, Enumeration, {"TryZip": _tryZipAsAt06a00ff(overwrites = True, keepsNone = True)})

    def test_the_report_benches_fall_when_none_is_not_kept_as_a_value(self) -> None:
        """As at 06a00ff, the second cause of 4.41 §4: _ZipInfo.SetValue stored GetNullableValue(info),
        so "equal lengths" read as "still running", and every comparison that walked two sequences of
        one length raised."""

        for bench, name in ((TestTheZipReportsTheLongerSide, "test_the_report_names_the_longer_side"),
                            (TestAreEqualsComparesBothSequencesToTheirEnds, "test_sequences_compare_item_by_item_in_order"),
                            (TestTheOrderedSetTupleComparesWholeIterables, "test_an_iterable_is_equal_only_to_the_same_items_in_the_same_order")):
            with self.subTest(bench = name): self.__assertFalls(bench, name, Enumeration, {"TryZip": _tryZipAsAt06a00ff(overwrites = False, keepsNone = False)})

    def test_the_refusal_bench_falls_when_the_report_answers_before_the_end(self) -> None:
        """No commit broke this one; the defect rebuilt is the likeliest way to break it: GetValue
        answering None, which reads as "equal lengths", where it has no value yet. IZipInfo carries
        GetValue, and the report the zip hands out does not override it."""

        def answering(self: Any) -> Any:
            value: INullable[bool|None] = self.TryGetValue()

            return value.GetValue() if value.HasValue() else None

        self.__assertFalls(TestTheZipReportsTheLongerSide, "test_the_report_is_refused_until_the_zip_has_ended", IZipInfo, {"GetValue": answering})

    def test_the_zip_bench_falls_as_it_stood_before_e69a028(self) -> None:
        """As at d4c9197: TryZip, which Zip looks up in its module."""

        self.__assertFalls(TestTheZipReportsTheLongerSide, "test_the_zip_pairs_every_item_and_an_absent_side_gives_no_zip", Enumeration, {"TryZip": _tryZipAsAtD4c9197})
