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
from typing import Any, Callable, NoReturn
from contextlib import ExitStack
from unittest import mock

from WinCopies.Collections import ReadOnlyArray, DuplicateKeyError
from WinCopies.Collections.Abstraction.Collection import SizedList, CreateList, CreateSortedList, TryCreateSizedList
from WinCopies.Collections.Abstraction.Mapping import CreateDictionary, CreateSet, Dictionary
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Abstraction.Selection import Converters
from WinCopies.Collections.Abstraction.Selection.Collection import CreateDictionary as CreateSelectionDictionary, Array as SelectionArray, List as SelectionList
from WinCopies.Collections.Circular import CircularList
import WinCopies.Collections.Abstract.Collection as AbstractCollection
import WinCopies.Collections.Abstraction.Mapping.Extensions as MappingExtensions
import WinCopies.Collections.Core as Core
import WinCopies.Collections.Range.Extensions as RangeExtensions
import WinCopies.Collections.Util as Util
from WinCopies.Collections.Util import GetDuplicateKeyError, GetDuplicateItemError, GetRepeatedItemError, GetDuplicateRangeError
from WinCopies.Collections.Core import IAbstractionSetterBase, ICollection, IDictionary
from WinCopies.Collections.Extensions.Collection import ReversedArrayBase
from WinCopies.Collections.ObjectModel.Collection import ObservableCollection
from WinCopies.Typing import INullable, GetNullable

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

_PAIRED_DICTIONARIES: ReadOnlyArray[tuple[str, _Factory]] = (
    ("Dictionary",            lambda: CreateDictionary({"a": 1, "b": 2})),
    ("Selection dictionary",  lambda: CreateSelectionDictionary(CreateDictionary({"a": 1, "b": 2}), Converters[int, int](int, int))))
"""The two dictionaries of _DICTIONARIES, holding the keys "a" and "b" rather than "a" alone, so that
a move can find its target taken and a swap two keys to exchange."""

_DICTIONARY_PAIRS: ReadOnlyArray[_Pair] = (
    ("Move", "TryMove", _TRIVALENT,
     (("('a', 'c')", lambda: ("a", "c")), ("('a', 'b')", lambda: ("a", "b")), ("('z', 'c')", lambda: ("z", "c")),
      ("('a', 'a')", lambda: ("a", "a")), ("('z', 'z')", lambda: ("z", "z")))),
    ("Swap", "TrySwap", _TRIVALENT,
     (("('a', 'b')", lambda: ("a", "b")), ("('a', 'z')", lambda: ("a", "z")), ("('a', 'a')", lambda: ("a", "a")), ("('z', 'z')", lambda: ("z", "z")))))
"""Moving and swapping by key on a dictionary holding "a" and "b": a move renames a key, so its target
must be free, and a swap exchanges the values of two keys it holds. Each in every shape the two tell
apart: a rename, a target taken, a source absent, the same key held, and the same key absent."""

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

    def test_on_every_dictionary(self) -> None:
        _assertChecks(self, _parityChecks(_PAIRED_DICTIONARIES, _DICTIONARY_PAIRS), lambda call: True)

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

def _contents(dictionary: Any) -> dict[Any, Any]:
    return {key: dictionary.GetAt(key) for key in dictionary.GetKeys().AsIterable()}

def _moved(contents: dict[Any, Any], x: Any, y: Any) -> dict[Any, Any]:
    result: dict[Any, Any] = dict(contents)

    result[y] = result.pop(x)

    return result

def _swapped(contents: dict[Any, Any], x: Any, y: Any) -> dict[Any, Any]:
    result: dict[Any, Any] = dict(contents)

    result[x], result[y] = result[y], result[x]

    return result

class TestADictionaryChangesPositionByKey(unittest.TestCase):
    """A move renames a key and a swap exchanges two values, answering as positions do elsewhere: True
    for a change, False for the same key held, None for a refusal, which leaves the dictionary as it
    was. The throwing forms raise KeyError naming the cause.

    Three defects lived here. Until 5500478 a move whose target was taken raised from its Try form
    and lost its source on the way, the source being removed before the target was refused. D-83,
    closed: once a move refused a target that exists, a key moved onto itself was refused too, None
    where the convention answers False, and Move raised with a false message. And the throwing forms
    raised IndexError, "Position a or b does not exist.", for keys that both existed when the move
    was refused for its target being taken."""

    def test_every_answer_follows_the_convention(self) -> None:
        rows: ReadOnlyArray[tuple[str, str, str, bool|None]] = (
            ("TryMove", "a", "c", True), ("TryMove", "a", "b", None), ("TryMove", "z", "c", None), ("TryMove", "a", "a", False), ("TryMove", "z", "z", None),
            ("TrySwap", "a", "b", True), ("TrySwap", "a", "z", None), ("TrySwap", "a", "a", False), ("TrySwap", "z", "z", None))

        for carrier, factory in _PAIRED_DICTIONARIES:
            for operation, x, y, expected in rows:
                with self.subTest(carrier = carrier, call = f"{operation}({x!r}, {y!r})"):
                    dictionary: Any = factory()
                    before: dict[Any, Any] = _contents(dictionary)

                    self.assertIs(getattr(dictionary, operation)(x, y), expected, f"{carrier}.{operation}({x!r}, {y!r})")

                    after: dict[Any, Any] = before if expected is not True else (_moved if operation == "TryMove" else _swapped)(before, x, y)

                    self.assertEqual(_contents(dictionary), after, f"{carrier}.{operation}({x!r}, {y!r}) left the wrong content")

    def test_a_refusal_raises_a_key_error_naming_its_cause(self) -> None:
        for carrier, factory in _PAIRED_DICTIONARIES:
            missing: str = str(factory()._GetKeyNotFoundError("z"))
            rows: ReadOnlyArray[tuple[str, str, str, str]] = (
                ("Move", "a", "b", str(DuplicateKeyError("Key b already exists."))),
                ("Move", "z", "c", missing), ("Move", "z", "b", missing), ("Move", "z", "z", missing),
                ("Swap", "a", "z", missing), ("Swap", "z", "a", missing), ("Swap", "z", "z", missing))

            for operation, x, y, message in rows:
                with self.subTest(carrier = carrier, call = f"{operation}({x!r}, {y!r})"):
                    dictionary: Any = factory()
                    before: dict[Any, Any] = _contents(dictionary)
                    raised: BaseException|None = _raised(lambda: getattr(dictionary, operation)(x, y))

                    self.assertIsInstance(raised, KeyError, f"{carrier}.{operation}({x!r}, {y!r})")
                    self.assertEqual(str(raised), message, f"{carrier}.{operation}({x!r}, {y!r}) named another cause")
                    self.assertEqual(_contents(dictionary), before, f"{carrier}.{operation}({x!r}, {y!r}) changed the dictionary while refusing")

_UNIQUE_LISTS: ReadOnlyArray[tuple[str, _Factory, int, int|None, bool]] = (
    ("OrderedSet.AsList()",                                lambda: CreateOrderedSet([0, 1, 2]).AsList(), 0, None, True),
    ("OrderedSet.AsList().AsReversed()",                   lambda: CreateOrderedSet([2, 1, 0]).AsList().AsReversed(), 0, None, False),
    (_OVER_SET,                                            lambda: CircularList[int](CreateOrderedSet([2, 0, 1]).AsList(), 1), 0, None, False),
    ("ObservableCollection over OrderedSet.AsList()",      lambda: ObservableCollection[int](CreateOrderedSet([0, 1, 2]).AsList()), 0, None, False),
    ("Selection.List, x + 10, over OrderedSet.AsList()",   lambda: SelectionList[int, int](CreateOrderedSet([0, 1, 2]).AsList(), Converters[int, int](lambda x: x + 10, lambda x: x - 10)), 10, 0, False))
"""Every list at hand that refuses a value it already holds, each reading three items of which the
first is the value given: the ordered set's view, and each kind of view or wrapper over it. The
fourth field is that value as the container holds it where a conversion stands between the two --
the value the container's own refusal names, which the converting layer tells again with the
caller's -- and None where none does. The last field says whether its slice route knows the cause
of a refusal; only the view itself does, the others asking CanSetRange, which answers without one."""

_UNIQUE_ARRAYS: ReadOnlyArray[tuple[str, _Factory, int, int|None]] = (
    ("OrderedSet.AsList().AsFixedSize()",                                lambda: CreateOrderedSet([0, 1, 2]).AsList().AsFixedSize(), 0, None),
    ("Selection.Array, x + 10, over OrderedSet.AsList().AsFixedSize()",  lambda: SelectionArray[int, int](CreateOrderedSet([0, 1, 2]).AsList().AsFixedSize(), Converters[int, int](lambda x: x + 10, lambda x: x - 10)), 10, 0))
"""The fixed-size view of the ordered set, which refuses a value it holds through its one write, SetAt,
and a converting array over it; the fields read as the first four of _UNIQUE_LISTS."""

def _innerRefusal(inner: int|None) -> DuplicateKeyError|None:
    return None if inner is None else GetDuplicateItemError(inner)

def _duplicateCalls(held: int, inner: int|None) -> ReadOnlyArray[tuple[str, Callable[[Any], Any], DuplicateKeyError, DuplicateKeyError|None]]:
    """Each call that gives a list a value it holds, with the error its refusal is expected to be -- an
    item already held, or a range refused as a whole, which names no item -- and its expected cause:
    the container's own refusal, which a converting layer tells again, or None where no conversion
    stands between or the range names no item to tell again."""

    fresh: int = held + 7
    item: DuplicateKeyError = GetDuplicateItemError(held)
    span: DuplicateKeyError = GetDuplicateRangeError()
    cause: DuplicateKeyError|None = _innerRefusal(inner)

    return (
        ("Add", lambda l: l.Add(held), item, cause), ("Insert", lambda l: l.Insert(0, held), item, cause), ("InsertRange", lambda l: l.InsertRange(0, [held]), span, None),
        ("AddRange, a value twice", lambda l: l.AddRange([fresh, fresh]), span, None), ("SetAt", lambda l: l.SetAt(1, held), item, cause),
        ("insert", lambda l: l.AsMutableSequence().insert(0, held), item, cause), ("append", lambda l: l.AsMutableSequence().append(held), item, cause),
        ("extend", lambda l: l.AsMutableSequence().extend([held]), span, None), ("[1] = x", lambda l: l.AsMutableSequence().__setitem__(1, held), item, cause))

class TestADuplicateRaisesADuplicateKeyError(unittest.TestCase):
    """D-47: a value or a key already held is refused with DuplicateKeyError, which is a KeyError, as the
    framework names every refusal bearing on a key, and a ValueError, as Python names a value it
    refuses. Until it, the same refusal raised KeyError by one route, a bare KeyError by the range
    routes, and ValueError by the Python path of the ordered set's view -- so that x[0] = 1 raised
    ValueError on the view and KeyError on a circular list over it. An absence keeps its own error,
    which must not be taken for this one."""

    def __assertRefuses(self, label: str, items: Any, act: Callable[[Any], Any], snapshot: Callable[[Any], Any] = _snapshot) -> None:
        before: Any = snapshot(items)
        raised: BaseException|None = _raised(lambda: act(items))

        self.assertIsInstance(raised, DuplicateKeyError, f"{label} raised {raised!r}")
        self.assertEqual(snapshot(items), before, f"{label} changed the collection while refusing")

    def test_a_set(self) -> None:
        calls: ReadOnlyArray[tuple[str, Callable[[Any], Any]]] = (
            ("Add(0)", lambda s: s.Add(0)), ("AddRange([0])", lambda s: s.AddRange([0])),
            ("AddRange([7, 7])", lambda s: s.AddRange([7, 7])), ("AddValues(0)", lambda s: s.AddValues(0)))

        for carrier, factory in _SETS:
            for label, call in calls:
                with self.subTest(carrier = carrier, call = label):
                    self.__assertRefuses(f"{carrier}.{label}", factory(), call)

    def test_a_dictionary(self) -> None:
        for carrier, factory in _DICTIONARIES:
            with self.subTest(carrier = carrier, call = "Add('a', 2)"):
                self.__assertRefuses(f"{carrier}.Add('a', 2)", factory(), lambda d: d.Add("a", 2), _contents)

        for carrier, factory in _PAIRED_DICTIONARIES:
            with self.subTest(carrier = carrier, call = "Move('a', 'b')"):
                self.__assertRefuses(f"{carrier}.Move('a', 'b')", factory(), lambda d: d.Move("a", "b"), _contents)

    def test_a_creation(self) -> None:
        for label, create in (("CreateSet([7, 7])", lambda: CreateSet([7, 7])), ("CreateOrderedSet([7, 7])", lambda: CreateOrderedSet([7, 7]))):
            with self.subTest(call = label):
                raised: BaseException|None = _raised(create)

                self.assertIsInstance(raised, DuplicateKeyError, f"{label} raised {raised!r}")

    def test_a_list(self) -> None:
        for carrier, factory, held, inner, _ in _UNIQUE_LISTS:
            for label, call, _, _ in _duplicateCalls(held, inner):
                with self.subTest(carrier = carrier, call = label):
                    self.__assertRefuses(f"{carrier}.{label}", factory(), call)

    def test_a_slice(self) -> None:
        """Only the view itself knows why it refuses a span. Through a view or a wrapper the slice
        route asks CanSetRange, whose answer is a boolean, and raises ValueError for any cause: that
        is the open point of D-47 on the cause of a span's refusal, asserted here as it stands so
        that settling it shows."""

        for carrier, factory, held, _, knowsTheCause in _UNIQUE_LISTS:
            with self.subTest(carrier = carrier):
                items: Any = factory()
                before: ReadOnlyArray[Any] = _snapshot(items)
                raised: BaseException|None = _raised(lambda: items.AsMutableSequence().__setitem__(slice(1, 2), [held]))

                if knowsTheCause: self.assertIsInstance(raised, DuplicateKeyError, f"{carrier}[1:2] = [x] raised {raised!r}")
                else: self.assertIs(type(raised), ValueError, f"{carrier}[1:2] = [x] raised {raised!r}")

                self.assertEqual(_snapshot(items), before, f"{carrier}[1:2] = [x] changed the list while refusing")

    def __assertAbsent(self, label: str, act: Callable[[], Any], expected: BaseException) -> None:
        with self.subTest(call = label):
            raised: BaseException|None = _raised(act)

            self.assertIsInstance(raised, type(expected), f"{label} raised {raised!r}")
            self.assertNotIsInstance(raised, DuplicateKeyError, f"{label} reports an absence as a duplicate")

            assert raised is not None

            self.assertEqual(raised.args, expected.args, f"{label} does not carry what is absent alone, as Python raises it")

    def test_an_absence_is_not_a_duplicate(self) -> None:
        """Nor does it carry a sentence: what is absent is its args[0], as Python raises it -- KeyError('z')
        for a dictionary, KeyError(9) for set.remove. Until D-47 the absence of a key alone carried
        "Key 9 not found.", which str() printed between quotes."""

        dictionaryCalls: ReadOnlyArray[tuple[str, Callable[[Any], Any]]] = (
            ("GetAt('z')", lambda d: d.GetAt("z")), ("Remove('z')", lambda d: d.Remove("z")), ("SetAt('z', 3)", lambda d: d.SetAt("z", 3)),
            ("Move('z', 'c')", lambda d: d.Move("z", "c")), ("Swap('a', 'z')", lambda d: d.Swap("a", "z")), ("Swap('z', 'a')", lambda d: d.Swap("z", "a")))

        for carrier, factory in _SETS: self.__assertAbsent(f"{carrier}.Remove(9)", lambda: factory().Remove(9), KeyError(9))

        for carrier, factory in _PAIRED_DICTIONARIES:
            for label, call in dictionaryCalls: self.__assertAbsent(f"{carrier}.{label}", lambda: call(factory()), KeyError("z"))

        for carrier, factory, _, _, _ in _UNIQUE_LISTS:
            self.__assertAbsent(f"{carrier}.GetAt(9)", lambda: factory().GetAt(9), IndexError(9))
            self.__assertAbsent(f"{carrier}.Remove(9)", lambda: factory().Remove(9), ValueError(9))

def _held(error: DuplicateKeyError) -> tuple[bool, object]:
    duplicate: INullable[object] = error.GetDuplicate()

    return (duplicate.HasValue(), duplicate.TryGetValue())

class TestADuplicateSaysItsCause(unittest.TestCase):
    """D-47: every refusal of a duplicate goes through the factory of its cause, so that one cause says
    one message and carries what is held twice. Until it, the same assignment said "Item 0 already
    exists at another position." on the ordered set's view and "Key 0 already exists." through any
    wrapper; a list named its value a key, which reads as its index; the same values given twice were
    told three ways by three routes; no error carried the item; and through a converting list or array
    a refusal named the container's value rather than the caller's. That layer now tells it again with
    the caller's value, the container's own refusal kept as its cause. The expectations are built
    through this module's own references to the factories, which a patch of the framework's leaves as
    they are."""

    def __assertSays(self, label: str, act: Callable[[], Any], expected: DuplicateKeyError, cause: DuplicateKeyError|None = None) -> None:
        with self.subTest(call = label):
            raised: BaseException|None = _raised(act)

            self.assertIsInstance(raised, DuplicateKeyError, f"{label} raised {raised!r}")

            assert isinstance(raised, DuplicateKeyError)

            self.assertEqual(str(raised), str(expected), f"{label} does not say its cause as its factory says it")
            self.assertEqual(_held(raised), _held(expected), f"{label} does not carry what is held twice")

            if cause is None: self.assertIsNone(raised.__cause__, f"{label} gives itself a cause, {raised.__cause__!r}")
            else:
                self.assertIsInstance(raised.__cause__, DuplicateKeyError, f"{label} does not keep the container's refusal as its cause")

                assert isinstance(raised.__cause__, DuplicateKeyError)

                self.assertEqual((str(raised.__cause__), _held(raised.__cause__)), (str(cause), _held(cause)), f"{label} keeps another cause than the container's refusal")

    def test_a_set(self) -> None:
        calls: ReadOnlyArray[tuple[str, Callable[[Any], Any], DuplicateKeyError]] = (
            ("Add(0)", lambda s: s.Add(0), GetDuplicateItemError(0)), ("AddRange([0])", lambda s: s.AddRange([0]), GetDuplicateRangeError()),
            ("AddRange([7, 7])", lambda s: s.AddRange([7, 7]), GetDuplicateRangeError()), ("AddValues(0)", lambda s: s.AddValues(0), GetDuplicateRangeError()))

        for carrier, factory in _SETS:
            for label, call, expected in calls: self.__assertSays(f"{carrier}.{label}", lambda: call(factory()), expected)

    def test_a_dictionary(self) -> None:
        for carrier, factory in _DICTIONARIES: self.__assertSays(f"{carrier}.Add('a', 2)", lambda: factory().Add("a", 2), GetDuplicateKeyError("a"))

        for carrier, factory in _PAIRED_DICTIONARIES: self.__assertSays(f"{carrier}.Move('a', 'b')", lambda: factory().Move("a", "b"), GetDuplicateKeyError("b"))

    def test_a_creation(self) -> None:
        for label, create in (("CreateSet([7, 7])", lambda: CreateSet([7, 7])), ("CreateOrderedSet([7, 7])", lambda: CreateOrderedSet([7, 7]))):
            self.__assertSays(label, create, GetRepeatedItemError(7))

    def test_a_list(self) -> None:
        """Through the slice route, only where it knows the cause: elsewhere it raises ValueError for
        any cause, which is D-47's point 4."""

        for carrier, factory, held, inner, knowsTheCause in _UNIQUE_LISTS:
            for label, call, expected, cause in _duplicateCalls(held, inner): self.__assertSays(f"{carrier}.{label}", lambda: call(factory()), expected, cause)

            if knowsTheCause:
                fresh: int = held + 7

                self.__assertSays(f"{carrier}[1:2] = [x]", lambda: factory().AsMutableSequence().__setitem__(slice(1, 2), [held]), GetDuplicateItemError(held))
                self.__assertSays(f"{carrier}[0:2] = [y, y]", lambda: factory().AsMutableSequence().__setitem__(slice(0, 2), [fresh, fresh]), GetRepeatedItemError(fresh))

    def test_an_array(self) -> None:
        for carrier, factory, held, inner in _UNIQUE_ARRAYS:
            self.__assertSays(f"{carrier}.SetAt(1, x)", lambda: factory().SetAt(1, held), GetDuplicateItemError(held), _innerRefusal(inner))

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

        def rebuilt(self: Any, key: int, value: Any) -> LookupError: return KeyError(f"Item {value} already exists at the {self.FindFirstIndex(value)} key.")

        target: Any = type(CreateOrderedSet([0]).AsList())

        self.__assertFalls((TestASetterAnswersByCause, "test_a_refused_value_is_reported_as_the_other_routes_report_it"), target, "_GetValueError", rebuilt)

    def test_the_setter_bench_falls_when_the_throwing_route_answers_what_setat_returns(self) -> None:
        """IAbstractionSetterBase._TrySetItemAt as it stood at 8a39df4."""

        def rebuilt(self: Any, items: Any, key: Any, value: Any, throwOnError: bool) -> Any: return (items.SetAt if throwOnError else items.TrySetItemAt)(key, value)

        self.__assertFalls((TestASetterAnswersByCause, "test_a_delegating_setter_answers_true_on_a_write_that_raises_when_refused"), IAbstractionSetterBase, "_TrySetItemAt", rebuilt)

    def test_the_dictionary_bench_falls_when_a_key_moved_onto_itself_is_refused(self) -> None:
        """_ChangePosition as it stood at 5500478, validating before comparing the two keys: D-83."""

        def rebuilt(x: Any, y: Any, collection: Any, validator: Any, updater: Any) -> bool|None:
            if validator(x, y):
                if x == y: return False

                updater(x, y)

                return True

            return None

        self.__assertFalls((TestADictionaryChangesPositionByKey, "test_every_answer_follows_the_convention"), Core, "_ChangePosition", rebuilt)

    def test_the_dictionary_bench_falls_when_a_move_takes_a_target_already_held(self) -> None:
        """A move validated on its source alone, as before 6c717bf, reaches the removal of its source
        before the target is refused."""

        def rebuilt(self: Any, x: Any, y: Any, move: bool = False) -> bool: return bool(self.ContainsKey(x) and (move or self.ContainsKey(y)))

        self.__assertFalls((TestADictionaryChangesPositionByKey, "test_every_answer_follows_the_convention"), IDictionary, "ValidateKeys", rebuilt)

    def test_the_dictionary_bench_falls_when_a_refusal_names_both_keys(self) -> None:
        """The key error of 615b507, which named both keys whatever the cause."""

        def rebuilt(self: Any, x: Any, y: Any) -> LookupError: return KeyError(f"Key {x} or {y} does not exist.")

        self.__assertFalls((TestADictionaryChangesPositionByKey, "test_a_refusal_raises_a_key_error_naming_its_cause"), IDictionary, "_GetKeysError", rebuilt)

    def __assertFallsWith(self, benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]], patches: ReadOnlyArray[tuple[Any, str, Any]]) -> None:
        """As __assertFalls, for a defect that lives under several names at once: a module-level
        function each importer holds its own reference to."""

        self.assertEqual(_fallen(_runBenches(benches)), 0, f"{benches} are expected to pass on the intact tree")

        with ExitStack() as stack:
            for target, name, rebuilt in patches: stack.enter_context(mock.patch.object(target, name, rebuilt))

            broken: unittest.TestResult = _runBenches(benches)


        self.assertGreater(_fallen(broken), 0, f"{benches} did not fall on the rebuilt defect")

    @staticmethod
    def __everywhere(rebuilt: Callable[[str], Any], names: ReadOnlyArray[str]) -> ReadOnlyArray[tuple[Any, str, Any]]:
        """Each named factory of a duplicate, rebuilt, under every module that holds it: Util, whose
        Throw forms build their error through it, and the three modules that build one directly."""

        holders: ReadOnlyArray[tuple[Any, ReadOnlyArray[str]]] = (
            (Util, ("GetDuplicateKeyError", "GetDuplicateItemError", "GetRepeatedItemError", "GetDuplicateRangeError")),
            (Core, ("GetDuplicateKeyError",)), (MappingExtensions, ("GetDuplicateItemError",)), (AbstractCollection, ("GetDuplicateItemError",)))

        return tuple((module, name, rebuilt(name)) for module, held in holders for name in held if name in names)

    def __assertEachFalls(self, bench: type[unittest.TestCase], tests: ReadOnlyArray[str], patches: ReadOnlyArray[tuple[Any, str, Any]]) -> None:
        for test in tests:
            with self.subTest(bench = test): self.__assertFallsWith(((bench, test),), patches)

    def test_the_duplicate_bench_falls_when_a_duplicate_raises_a_plain_key_error(self) -> None:
        """The factories of a duplicate building a plain KeyError, as GetKeyError did until 8e4000a."""

        def rebuilt(name: str) -> Callable[..., KeyError]:
            original: Callable[..., DuplicateKeyError] = getattr(Util, name)

            def plain(*args: Any) -> KeyError: return KeyError(str(original(*args)))

            return plain

        self.__assertEachFalls(TestADuplicateRaisesADuplicateKeyError, ("test_a_set", "test_a_dictionary", "test_a_creation", "test_a_list"),
                               self.__everywhere(rebuilt, ("GetDuplicateKeyError", "GetDuplicateItemError", "GetRepeatedItemError", "GetDuplicateRangeError")))

    def test_the_cause_bench_falls_on_the_wording_of_get_key_error(self) -> None:
        """The wording of GetKeyError as it stood until the factories of a duplicate, the item kept: an
        item named a key, and the values given twice told otherwise than the slice told them."""

        def item(item: Any) -> DuplicateKeyError: return DuplicateKeyError(f"Key {item} already exists.", GetNullable(item))
        def repeated(item: Any) -> DuplicateKeyError: return DuplicateKeyError(f"Item '{item}' has a duplicate.", GetNullable(item))

        wording: dict[str, Callable[[Any], DuplicateKeyError]] = {"GetDuplicateItemError": item, "GetRepeatedItemError": repeated}

        self.__assertEachFalls(TestADuplicateSaysItsCause, ("test_a_set", "test_a_creation", "test_a_list"), self.__everywhere(wording.__getitem__, tuple(wording)))

    def test_the_cause_bench_falls_when_an_assignment_says_its_own_message(self) -> None:
        """SetOrderedValue as it stood until the factories of a duplicate: it told a value held at another
        position in words of its own, so that the same assignment said one thing on the view and another
        through any wrapper."""

        def rebuilt(value: Any) -> NoReturn: raise DuplicateKeyError(f"Item {value} already exists at another position.", GetNullable(value))

        self.__assertFallsWith(((TestADuplicateSaysItsCause, "test_a_list"),), ((RangeExtensions, "ThrowDuplicateItemError", rebuilt),))

    def test_the_cause_bench_falls_when_a_factory_forgets_the_item(self) -> None:
        """The factories of a duplicate saying the item without carrying it, as every duplicate error did
        until them."""

        def rebuilt(name: str) -> Callable[..., DuplicateKeyError]:
            original: Callable[..., DuplicateKeyError] = getattr(Util, name)

            def forgetful(*args: Any) -> DuplicateKeyError: return DuplicateKeyError(str(original(*args)))

            return forgetful

        self.__assertEachFalls(TestADuplicateSaysItsCause, ("test_a_set", "test_a_dictionary", "test_a_creation", "test_a_list"),
                               self.__everywhere(rebuilt, ("GetDuplicateKeyError", "GetDuplicateItemError", "GetRepeatedItemError")))

    def test_the_cause_bench_falls_when_a_converting_layer_hands_the_refusal_on(self) -> None:
        """The writes of a converting layer as they stood until M3, which let the container's refusal
        through as it was, naming the container's value rather than the caller's."""

        def rebuilt(write: Callable[[], object], value: object) -> None: write()

        self.__assertEachFalls(TestADuplicateSaysItsCause, ("test_a_list", "test_an_array"), ((AbstractCollection, "_Write", rebuilt),))

    def test_the_cause_bench_falls_when_a_converting_layer_drops_the_container_refusal(self) -> None:
        """A converting layer that tells the refusal again with the caller's value, but from None, so
        that the container's own refusal is lost."""

        def rebuilt(write: Callable[[], object], value: object) -> None:
            try: write()
            except DuplicateKeyError as error:
                if not error.GetDuplicate().HasValue(): raise

                raise GetDuplicateItemError(value) from None

        self.__assertEachFalls(TestADuplicateSaysItsCause, ("test_a_list", "test_an_array"), ((AbstractCollection, "_Write", rebuilt),))

    def test_the_duplicate_bench_falls_when_a_range_raises_a_bare_key_error(self) -> None:
        """ISet.AddRange as it stood at 8e4000a."""

        def rebuilt(self: Any, items: Any) -> None:
            if self.TryAddRange(items) is None: raise KeyError()

        self.__assertFallsWith(((TestADuplicateRaisesADuplicateKeyError, "test_a_set"),), ((Core.ISet, "AddRange", rebuilt),))

    def test_the_duplicate_bench_falls_when_the_python_path_raises_a_plain_value_error(self) -> None:
        """The Python path of the ordered set's view as it stood at 8e4000a."""

        original: Any = RangeExtensions.SetOrderedItems

        def rebuilt(*args: Any) -> Any:
            try: return original(*args)
            except DuplicateKeyError as error: raise ValueError(str(error))

        self.__assertFallsWith(((TestADuplicateRaisesADuplicateKeyError, "test_a_list"), (TestADuplicateRaisesADuplicateKeyError, "test_a_slice")),
                               ((MappingExtensions, "SetOrderedItems", rebuilt),))

    def test_the_absence_bench_falls_when_an_absence_raises_a_duplicate_key_error(self) -> None:
        """A factory of the absent key that would build the type of a duplicate."""

        original: Any = Util.GetKeyNotFoundError

        def rebuilt(key: Any) -> KeyError: return DuplicateKeyError(str(original(key)))

        self.__assertFallsWith(((TestADuplicateRaisesADuplicateKeyError, "test_an_absence_is_not_a_duplicate"),), tuple((module, "GetKeyNotFoundError", rebuilt) for module in (Util, Core)))

    def test_the_absence_bench_falls_when_an_absence_carries_a_sentence(self) -> None:
        """The factory of the absent key as it stood until D-47, which carried a sentence rather than the key."""

        def rebuilt(key: Any) -> KeyError: return KeyError(f"Key {key} not found.")

        self.__assertFallsWith(((TestADuplicateRaisesADuplicateKeyError, "test_an_absence_is_not_a_duplicate"),), tuple((module, "GetKeyNotFoundError", rebuilt) for module in (Util, Core)))
