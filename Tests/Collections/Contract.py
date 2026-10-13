"""
Contract benches for the Try forms, asserted on every carrier at hand.

Since the IList hooks were split in two -- _TryInsert and _Insert, _TryInsertRange and
_InsertRange -- each operation reaches its implementation through two doors, and an implementer
writes both. That is what lets the throwing form name its own cause, which a form derived from
the Try one could not. It is also what lets the two drift apart, and D-71's second layer was
exactly that: on the circular list, once its recursion was lifted, the Try form wrote at the
right position and the throwing form at another. Nothing in the suite compared the two doors;
the first bench here does.

The second asserts the table D-57 settled for every range insertion: True inserted, False an
empty range, None refused. ICollection.TryAddRange followed the inverse convention for one
commit, ff69598, and no bench saw it.
"""

import unittest
from collections.abc import Iterator
from typing import Any, Callable
from unittest import mock

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import SizedList, CreateList, CreateSortedList, TryCreateSizedList
from WinCopies.Collections.Abstraction.Mapping import CreateDictionary, CreateSet, Dictionary
from WinCopies.Collections.Util import GetKeyValueError
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Abstraction.Selection import Converters
from WinCopies.Collections.Abstraction.Selection.Collection import CreateDictionary as CreateSelectionDictionary, List as SelectionList
from WinCopies.Collections.Circular import CircularList
from WinCopies.Collections.Core import IAbstractionSetterBase, ICollection
from WinCopies.Collections.Extensions.Collection import ReversedArrayBase
from WinCopies.Collections.ObjectModel.Collection import ObservableCollection

type _Factory = Callable[[], Any]
type _Arguments = Callable[[], tuple[Any, ...]]
type _Answer = bool|None
type _Contract = tuple[frozenset[_Answer], frozenset[_Answer]]
type _Pair = tuple[str, str, _Contract, ReadOnlyArray[tuple[str, _Arguments]]]

def _sizedList(capacity: int, content: list[int]|None = None) -> Any:
    items: Any = TryCreateSizedList(capacity, [0, 1, 2] if content is None else content)

    assert items is not None

    return items

_OVER_FULL: str = "CircularList over a full SizedList"
_OVER_SET: str = "CircularList over OrderedSet.AsList()"

_LISTS: ReadOnlyArray[tuple[str, _Factory]] = (
    ("List",                             lambda: CreateList([0, 1, 2])),
    ("SizedList, spare capacity",        lambda: _sizedList(5)),
    ("SizedList, full",                  lambda: _sizedList(3)),
    ("ObservableCollection",             lambda: ObservableCollection[int](CreateList([0, 1, 2]))),
    ("List.AsReversed()",                lambda: CreateList([2, 1, 0]).AsReversed()),
    ("OrderedSet.AsList()",              lambda: CreateOrderedSet([0, 1, 2]).AsList()),
    ("OrderedSet.AsList().AsReversed()", lambda: CreateOrderedSet([2, 1, 0]).AsList().AsReversed()),
    ("Selection.List",                   lambda: SelectionList[int, int](CreateList([0, 1, 2]), Converters[int, int](int, int))),
    ("CircularList, start 1",            lambda: CircularList[int](CreateList([2, 0, 1]), 1)),
    (_OVER_FULL,                         lambda: CircularList[int](_sizedList(3, [2, 0, 1]), 1)),
    (_OVER_SET,                          lambda: CircularList[int](CreateOrderedSet([2, 0, 1]).AsList(), 1)))
"""Every constructible IList at hand, each reading (0, 1, 2), so that one table of calls means
the same thing on all of them. The full SizedList is the carrier that refuses for capacity, the
two ordered set views those that refuse for unicity, the converting list the one that projects
its items, and the circular lists those whose hooks translate every position.

A carrier counts for what it can refuse. The circular list over a free List never refuses
anything but an index, so it could not show what the circular hooks do with a refusal -- and
D-74, a Try form answering True to every refusal, passed this table while only that carrier
stood for the circular family. The two circular carriers over a refusing container are there
for that reason."""

_SETS: ReadOnlyArray[tuple[str, _Factory]] = (
    ("Set",        lambda: CreateSet([0, 1, 2])),
    ("OrderedSet", lambda: CreateOrderedSet([0, 1, 2])))

# What each Try form may answer, as (refusals, nothing to do). The throwing twin raises on a
# refusal and on nothing else, which is read off the twin's own definition rather than chosen
# here: Insert raises on False, InsertRange and Move on None, RemoveAt on anything but True.
_BIVALENT: _Contract = (frozenset((False,)), frozenset())
_TRIVALENT: _Contract = (frozenset((None,)), frozenset((False,)))
_REMOVAL: _Contract = (frozenset((False, None)), frozenset())
# SetAt raises on both refusals TrySetItemAt tells apart: None for a key it does not hold, False
# for a value it refuses at a key it holds.
_SETTER: _Contract = (frozenset((False, None)), frozenset())

_LIST_PAIRS: ReadOnlyArray[_Pair] = (
    ("Insert", "TryInsert", _BIVALENT,
     (("(1, 7)", lambda: (1, 7)), ("(3, 7)", lambda: (3, 7)), ("(9, 7)", lambda: (9, 7)), ("(1, 0)", lambda: (1, 0)))),
    ("InsertRange", "TryInsertRange", _TRIVALENT,
     (("(1, [7, 8])", lambda: (1, [7, 8])), ("(3, [7])", lambda: (3, [7])), ("(1, [])", lambda: (1, [])),
      ("(9, [7])", lambda: (9, [7])), ("(1, [0])", lambda: (1, [0])), ("(1, [7, 7])", lambda: (1, [7, 7])),
      ("(1, iter([7, 8]))", lambda: (1, iter([7, 8]))))),
    ("Add", "TryAdd", _BIVALENT,
     (("(7)", lambda: (7,)), ("(0)", lambda: (0,)))),
    ("AddRange", "TryAddRange", _TRIVALENT,
     (("([7, 8])", lambda: ([7, 8],)), ("([])", lambda: ([],)), ("([0])", lambda: ([0],)), ("([7, 7])", lambda: ([7, 7],)))),
    ("SetAt", "TrySetAt", _BIVALENT,
     (("(1, 7)", lambda: (1, 7)), ("(1, 1)", lambda: (1, 1)), ("(9, 7)", lambda: (9, 7)), ("(1, 0)", lambda: (1, 0)))),
    ("SetAt", "TrySetItemAt", _SETTER,
     (("(1, 7)", lambda: (1, 7)), ("(1, 1)", lambda: (1, 1)), ("(9, 7)", lambda: (9, 7)), ("(-1, 7)", lambda: (-1, 7)), ("(1, 0)", lambda: (1, 0)))),
    ("RemoveAt", "TryRemoveAt", _REMOVAL,
     (("(1)", lambda: (1,)), ("(9)", lambda: (9,)))),
    ("RemoveRange", "TryRemoveRange", _BIVALENT,
     (("(0, 2)", lambda: (0, 2)), ("(9, 1)", lambda: (9, 1)))),
    ("Remove", "TryRemove", _BIVALENT,
     (("(1)", lambda: (1,)), ("(9)", lambda: (9,)))),
    ("Move", "TryMove", _TRIVALENT,
     (("(0, 2)", lambda: (0, 2)), ("(1, 1)", lambda: (1, 1)), ("(0, 9)", lambda: (0, 9)))),
    ("Swap", "TrySwap", _TRIVALENT,
     (("(0, 2)", lambda: (0, 2)), ("(1, 1)", lambda: (1, 1)), ("(0, 9)", lambda: (0, 9)))))
"""Every Try form of the list surface beside its throwing twin, in each argument shape the
carriers tell apart: inside, the append position, an index outside, a value the ordered set
already holds, an empty range, a range carrying a duplicate, and a one-pass iterable."""

_SET_PAIRS: ReadOnlyArray[_Pair] = (
    ("Add", "TryAdd", _BIVALENT,
     (("(7)", lambda: (7,)), ("(0)", lambda: (0,)))),
    ("AddRange", "TryAddRange", _TRIVALENT,
     (("([7, 8])", lambda: ([7, 8],)), ("([])", lambda: ([],)), ("([0])", lambda: ([0],)), ("([7, 7])", lambda: ([7, 7],)))),
    ("Remove", "TryRemove", _BIVALENT,
     (("(1)", lambda: (1,)), ("(9)", lambda: (9,)))))

_BLOCKED: ReadOnlyArray[tuple[str, ReadOnlyArray[tuple[str, str]]]] = ()
"""Checks that an open defect still breaks, named with their carrier and grouped by defect, as in
Mapping.py; the labels are those of either bench below. None is open today.

Two groups have left on closing. D-73: the circular list's TryRemoveAt and TryRemove refused by
raising, and answer since d4f974a. D-74: on the Try path the circular insertion helper folded a
refused insertion into the answer that meant "inserted, no shift of the start", and an insertion
into an empty source discarded the container's answer, so every refusal answered True with the
content untouched; its 23 checks on the two circular carriers over a refusing container are
asserted by the benches below since the helper keeps the two apart."""

def _blocked() -> frozenset[tuple[str, str]]:
    return frozenset(call for _, calls in _BLOCKED for call in calls)

def _snapshot(items: Any) -> ReadOnlyArray[Any]:
    return tuple(items.AsIterable())

def _calls(carriers: ReadOnlyArray[tuple[str, _Factory]], pairs: ReadOnlyArray[_Pair]) -> Iterator[tuple[str, _Factory, str, _Pair, _Arguments]]:
    for carrier, factory in carriers:
        for pair in pairs:
            for label, arguments in pair[3]:
                yield (carrier, factory, f"{pair[1]}/{pair[0]}{label}", pair, arguments)

type _Check = Callable[[], str|None]

def _diverge(factory: _Factory, pair: _Pair, arguments: _Arguments) -> str|None:
    """How the two doors disagree on one call, or None when they agree.

    Each form runs on a carrier of its own, so neither sees what the other did. The Try form
    may not raise at all; a refusal raises through the throwing form and leaves both carriers
    as they were; nothing to do raises through neither and leaves them as they were; a success
    leaves the two carriers with the same content.
    """

    throwing, trying, (refusals, nothing), _ = pair
    tried: Any = factory()
    thrown: Any = factory()
    before: ReadOnlyArray[Any] = _snapshot(tried)
    raised: Exception|None = None

    try: answer: Any = getattr(tried, trying)(*arguments())
    except Exception as exception: return f"the Try form raised {exception!r}"

    try: getattr(thrown, throwing)(*arguments())
    except Exception as exception: raised = exception

    if answer is True:
        if raised is not None: return f"the Try form answered True and the throwing one raised {raised!r}"

        return None if _snapshot(tried) == _snapshot(thrown) else f"the Try form left {_snapshot(tried)} and the throwing one {_snapshot(thrown)}"

    if answer in refusals:
        if raised is None: return f"the Try form refused with {answer!r} and the throwing one went through, leaving {_snapshot(thrown)}"

    elif answer in nothing:
        if raised is not None: return f"the Try form answered {answer!r}, nothing to do, and the throwing one raised {raised!r}"

    else: return f"the Try form answered {answer!r}, which its contract does not allow"

    if _snapshot(tried) != before or _snapshot(thrown) != before:
        return f"no write was due, yet the carriers hold {_snapshot(tried)} and {_snapshot(thrown)}"

    return None

def _parityCheck(factory: _Factory, pair: _Pair, arguments: _Arguments) -> _Check:
    return lambda: _diverge(factory, pair, arguments)

def _parityChecks(carriers: ReadOnlyArray[tuple[str, _Factory]], pairs: ReadOnlyArray[_Pair]) -> Iterator[tuple[str, str, _Check]]:
    for carrier, factory, call, pair, arguments in _calls(carriers, pairs):
        yield (carrier, call, _parityCheck(factory, pair, arguments))

def _assertChecks(test: unittest.TestCase, checks: Iterator[tuple[str, str, _Check]], selected: Callable[[tuple[str, str]], bool]) -> None:
    for carrier, call, check in checks:
        if not selected((carrier, call)): continue

        with test.subTest(carrier = carrier, call = call):
            failure: str|None = check()

            test.assertIsNone(failure, f"{carrier}, {call}: {failure}")

class TestTryFormsAgreeWithTheirThrowingForms(unittest.TestCase):
    """One request through the two doors of one operation, on every carrier.

    The Try form says yes, no or nothing to do; the throwing form has to say the same thing in
    its own way. A disagreement is a caller who gets a write by one door and a refusal by the
    other, or two different writes for one request.
    """

    def test_on_every_list(self) -> None:
        blocked: frozenset[tuple[str, str]] = _blocked()

        _assertChecks(self, _parityChecks(_LISTS, _LIST_PAIRS), lambda call: call not in blocked)

    def test_on_every_set(self) -> None:
        _assertChecks(self, _parityChecks(_SETS, _SET_PAIRS), lambda call: True)

_REFUSED_RANGES: dict[str, list[int]] = {
    "SizedList, full": [7],
    "OrderedSet.AsList()": [0],
    "OrderedSet.AsList().AsReversed()": [0],
    _OVER_FULL: [7],
    _OVER_SET: [0],
    "Set": [0],
    "OrderedSet": [0]}
"""The range each refusing carrier turns down: one that overflows its capacity, or one that
carries a value the set already holds. The other carriers take any range."""

def _rangeAnswers(carrier: str, collection: bool, positional: bool) -> ReadOnlyArray[tuple[str, Callable[[Any], Any], _Answer]]:
    """What the table of D-57 says each range insertion answers on `carrier`.

    The answer to an index outside combined with an empty range is left out on purpose: the
    code checks the index first and answers None, but no arbitration says which of the two
    should win, and a bench is not the place to make one.
    """

    refused: list[int]|None = _REFUSED_RANGES.get(carrier)
    answers: list[tuple[str, Callable[[Any], Any], _Answer]] = [
        ("TryAddRange([])",       lambda c: c.TryAddRange([]),       False),
        ("TryAddRange(iter([]))", lambda c: c.TryAddRange(iter([])), False),
        ("TryAddRange([7, 8])",   lambda c: c.TryAddRange([7, 8]),   True) if refused is None else
        (f"TryAddRange({refused})", lambda c: c.TryAddRange(list(refused)), None)]

    # ICollection takes None for nothing to add; ISet's signature does not admit it.
    if collection: answers.append(("TryAddRange(None)", lambda c: c.TryAddRange(None), False))

    if positional:
        insertions: list[tuple[str, Callable[[Any], Any], _Answer]] = [
            ("TryInsertRange(1, [])",  lambda c: c.TryInsertRange(1, []),      False),
            ("TryInsertRange(9, [7])", lambda c: c.TryInsertRange(9, [7]),     None),
            ("TryInsertRange(1, [7])", lambda c: c.TryInsertRange(1, [7]),     True) if refused is None else
            (f"TryInsertRange(1, {refused})", lambda c: c.TryInsertRange(1, list(refused)), None)]

        answers += insertions

    return tuple(answers)

def _trivalenceCheck(factory: _Factory, act: Callable[[Any], Any], expected: _Answer) -> _Check:
    def check() -> str|None:
        try: answer: Any = act(factory())
        except Exception as exception: return f"raised {exception!r}"

        return None if answer is expected else f"answered {answer!r}, the table says {expected!r}"

    return check

def _trivalenceChecks(carriers: ReadOnlyArray[tuple[str, _Factory]], collection: bool, positional: bool) -> Iterator[tuple[str, str, _Check]]:
    for carrier, factory in carriers:
        for call, act, expected in _rangeAnswers(carrier, collection, positional):
            yield (carrier, call, _trivalenceCheck(factory, act, expected))

class TestRangeInsertionTrivalence(unittest.TestCase):
    """D-57's table, on every range insertion of every carrier: True inserted, False an empty
    range, None refused whatever the cause. The identity is asserted, not the truth value:
    False and None are both falsy, and telling them apart is the whole point of the table."""

    def __run(self, carriers: ReadOnlyArray[tuple[str, _Factory]], collection: bool, positional: bool) -> None:
        blocked: frozenset[tuple[str, str]] = _blocked()

        _assertChecks(self, _trivalenceChecks(carriers, collection, positional), lambda call: call not in blocked)

    def test_on_every_list(self) -> None:
        self.__run(_LISTS, True, True)

    def test_on_the_sorted_list(self) -> None:
        """The one ICollection that is not an IList: it has no range primitive and never
        refuses, so only the empty range and the accepted one are asked of it."""

        self.__run((("SortedList", lambda: CreateSortedList([0, 1, 2])),), True, False)

    def test_on_every_set(self) -> None:
        self.__run(_SETS, False, False)

_UNIQUE: frozenset[str] = frozenset(("OrderedSet.AsList()", "OrderedSet.AsList().AsReversed()", _OVER_SET))
"""The list carriers that refuse a value they already hold, the one refusal a setter can make at a
key it holds."""

_DICTIONARIES: ReadOnlyArray[tuple[str, _Factory]] = (
    ("Dictionary",            lambda: CreateDictionary({"a": 1})),
    ("Selection dictionary",  lambda: CreateSelectionDictionary(CreateDictionary({"a": 1}), Converters[int, int](int, int))))
"""A dictionary and a converting one over it, each holding the key "a" and not the key "b"."""

def _raised(act: Callable[[], Any]) -> BaseException|None:
    try: act()
    except Exception as exception: return exception

    return None

class TestASetterAnswersByCause(unittest.TestCase):
    """TrySetItemAt answers in three values, read off IDefaultSetter: True for a write, None for a
    key the collection does not hold, False for a value it refuses at a key it holds. SetAt raises
    on both refusals, and names what the caller passed.

    D-81, closed: a reversed view handed the converted index to its source without validating the
    caller's, so the source refused that one and named it: SetAt(9, 7) raised IndexError(-7) on a
    view of three items. D-82, closed: a dictionary answered False for a key it does not hold, the
    answer that means a refused value, and its SetAt raised its own message rather than the one of
    the key error hook."""

    def test_every_list_answers_by_cause(self) -> None:
        for carrier, factory in _LISTS:
            causes: ReadOnlyArray[tuple[str, tuple[int, int], bool|None]] = (
                ("a write", (1, 7), True),
                ("an index out of range", (9, 7), None),
                ("a negative index", (-1, 7), None),
                ("a value held elsewhere", (1, 0), False if carrier in _UNIQUE else True))

            for cause, (index, value), expected in causes:
                with self.subTest(carrier = carrier, cause = cause):
                    self.assertIs(factory().TrySetItemAt(index, value), expected, f"{carrier}.TrySetItemAt{(index, value)}")

    def test_the_index_error_names_the_index_passed(self) -> None:
        for carrier, factory in _LISTS:
            for index in (9, 3, -1):
                with self.subTest(carrier = carrier, index = index):
                    raised: BaseException|None = _raised(lambda: factory().SetAt(index, 7))

                    self.assertIsInstance(raised, IndexError, f"{carrier}.SetAt({index}, 7)")
                    self.assertEqual(getattr(raised, "args", None), (index,), f"{carrier}.SetAt({index}, 7) named another index")

    def test_every_dictionary_answers_by_cause(self) -> None:
        for carrier, factory in _DICTIONARIES:
            with self.subTest(carrier = carrier):
                self.assertIs(factory().TrySetItemAt("a", 2), True, f"{carrier}.TrySetItemAt('a', 2)")
                self.assertIsNone(factory().TrySetItemAt("b", 2), f"{carrier}.TrySetItemAt('b', 2)")

                raised: BaseException|None = _raised(lambda: factory().SetAt("b", 2))

                self.assertIsInstance(raised, KeyError, f"{carrier}.SetAt('b', 2)")
                self.assertEqual(str(raised), str(factory()._GetKeyNotFoundError("b")), f"{carrier}.SetAt('b', 2) bypassed the key error hook")

    def test_a_refused_value_is_reported_as_the_other_routes_report_it(self) -> None:
        """SetAt names the value it refuses as Add does for the same cause, without a position: a
        position read in the container is not the caller's once a reversed or circular view stands
        between them."""

        for carrier, factory in _LISTS:
            if carrier not in _UNIQUE: continue

            with self.subTest(carrier = carrier):
                raised: BaseException|None = _raised(lambda: factory().SetAt(1, 0))
                reference: BaseException|None = _raised(lambda: factory().Add(0))

                self.assertIsInstance(raised, KeyError, f"{carrier}.SetAt(1, 0)")
                self.assertEqual(str(raised), str(reference), f"{carrier}.SetAt(1, 0) and Add(0) report the same refusal differently")

    def test_a_delegating_setter_answers_true_on_a_write_that_raises_when_refused(self) -> None:
        """A view that hands a write to its source answers on the throwing route what it answers on
        the other: True for a write, whatever the source's SetAt returns."""

        delegating: ReadOnlyArray[tuple[str, _Factory, Any, Any]] = (
            *((carrier, factory, 1, 7) for carrier, factory in _LISTS if carrier.endswith("AsReversed()")),
            ("Selection dictionary", _DICTIONARIES[1][1], "a", 2))

        for carrier, factory, key, value in delegating:
            with self.subTest(carrier = carrier):
                self.assertIs(factory()._TrySetAt(key, value, True), True, f"{carrier}._TrySetAt({key!r}, {value!r}, True)")

class TestChecksBrokenByOpenDefects(unittest.TestCase):
    """The checks _BLOCKED holds out, one bench per defect, so that each signals as an
    unexpected success the day its defect closes, rather than staying excluded in silence. A
    group may hold checks of either bench."""

    def _assertGroupPasses(self, defect: str) -> None:
        calls: ReadOnlyArray[tuple[str, str]] = next(group for name, group in _BLOCKED if name.startswith(defect))

        def checks() -> Iterator[tuple[str, str, _Check]]:
            yield from _parityChecks(_LISTS, _LIST_PAIRS)
            yield from _trivalenceChecks(_LISTS, True, True)

        _assertChecks(self, checks(), lambda call: call in calls)

def _runBenches(benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]]) -> unittest.TestResult:
    """Runs the named benches through a real result object, as Registry.py does, so that every
    sub-test that falls is counted."""

    result: unittest.TestResult = unittest.TestResult()

    unittest.TestSuite(benchType(name) for benchType, name in benches).run(result)

    return result

def _fallen(result: unittest.TestResult) -> int:
    return len(result.failures) + len(result.errors)

class TestTheseBenchesCanFail(unittest.TestCase):
    """A green bench is worth nothing unless it can go red, so each one above is run against a
    rebuilt defect: green on the intact tree, red on the rebuilt one. The substitutions are class
    attributes, patched for the length of a block and restored on the way out; the control is
    sound only on a single-threaded run, which is how the suite runs."""

    def __assertFalls(self, bench: tuple[type[unittest.TestCase], str], target: Any, name: str, rebuilt: Any) -> None:
        self.assertEqual(_fallen(_runBenches((bench,))), 0, f"{bench[1]} is expected to pass on the intact tree")

        with mock.patch.object(target, name, rebuilt): broken: unittest.TestResult = _runBenches((bench,))

        self.assertGreater(_fallen(broken), 0, f"{bench[1]} did not fall on the rebuilt defect")

    def test_the_parity_bench_falls_when_the_doors_disagree(self) -> None:
        """A Try door that answers True without writing, on the one carrier that refuses for
        capacity: the throwing door writes where it should, or raises where the Try one did not
        refuse. Both are divergences, and neither is visible to a bench that reads one door."""

        def rebuilt(self: Any, index: int, items: Any) -> bool: return True

        self.__assertFalls((TestTryFormsAgreeWithTheirThrowingForms, "test_on_every_list"), SizedList, "_TryInsertRange", rebuilt)

    def test_the_trivalence_bench_falls_on_the_inverse_convention(self) -> None:
        """ICollection.TryAddRange as it stood at ff69598: None for an empty range, False for a
        refusal, the inverse of the table."""

        def rebuilt(self: Any, items: Any) -> Any:
            normalized: Any = self._NormalizeItems(items)

            return None if normalized is None else self._TryAddRange(normalized)

        self.__assertFalls((TestRangeInsertionTrivalence, "test_on_every_list"), ICollection, "TryAddRange", rebuilt)

    def test_the_setter_bench_falls_when_a_reversed_view_hands_on_an_unchecked_index(self) -> None:
        """ReversedArrayBase._TrySetAt as it stood at cded13a, delegating before validating."""

        def rebuilt(self: Any, key: int, value: Any, throwOnError: bool) -> Any: return self._TrySetItemAt(self._GetSpecializedContainer(), self.ReverseIndex(key), value, throwOnError)

        self.__assertFalls((TestASetterAnswersByCause, "test_the_index_error_names_the_index_passed"), ReversedArrayBase, "_TrySetAt", rebuilt)

    def test_the_setter_bench_falls_when_a_dictionary_answers_false_for_a_missing_key(self) -> None:
        """Dictionary._TrySetAt as it stood at cded13a."""

        def rebuilt(self: Any, key: Any, value: Any, throwOnError: bool) -> Any:
            if key in self.GetKeys().AsIterable(): return True

            if throwOnError: raise KeyError(f"Key {key} not found.")

            return False

        self.__assertFalls((TestASetterAnswersByCause, "test_every_dictionary_answers_by_cause"), Dictionary, "_TrySetAt", rebuilt)

    def test_the_setter_bench_falls_when_a_refused_value_names_the_container_position(self) -> None:
        """The ordered set view's value error as it stood at 8a39df4."""

        def rebuilt(self: Any, key: int, value: Any) -> LookupError: return GetKeyValueError(self.FindFirstIndex(value), value)

        target: Any = type(CreateOrderedSet([0]).AsList())

        self.__assertFalls((TestASetterAnswersByCause, "test_a_refused_value_is_reported_as_the_other_routes_report_it"), target, "_GetValueError", rebuilt)

    def test_the_setter_bench_falls_when_the_throwing_route_answers_what_setat_returns(self) -> None:
        """IAbstractionSetterBase._TrySetItemAt as it stood at 8a39df4."""

        def rebuilt(self: Any, items: Any, key: Any, value: Any, throwOnError: bool) -> Any: return (items.SetAt if throwOnError else items.TrySetItemAt)(key, value)

        self.__assertFalls((TestASetterAnswersByCause, "test_a_delegating_setter_answers_true_on_a_write_that_raises_when_refused"), IAbstractionSetterBase, "_TrySetItemAt", rebuilt)
