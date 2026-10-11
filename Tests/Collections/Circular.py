"""
Conformance of the circular list to a model of what it means.

A circular list reads its container from a start and wraps around: over (2, 0, 1) with start 1
it reads (0, 1, 2). Every structural change therefore has two parts, the change to the container
and the change to the start, and the second is the one that went wrong. D-71 left the start where
it was after an insertion before the physical head, D-72 left it past the count after a first
insertion into an empty source, and D-73 left it in place after a removal before the head. Each
was invisible to any bench that read one carrier at one start, because the content comes out
right whenever the position lands after the head.

So the benches here compare every insertion and every removal, at every logical index and every
start, against a Python list holding the logical content, and assert as well that the start
stays inside the container. The reference is computed, never written by hand.
"""

import unittest
from collections.abc import Iterator
from typing import Any, Callable
from unittest import mock

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import CreateList, TryCreateSizedList
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Circular import CircularList

type _Act = Callable[[Any], Any]
type _Model = Callable[[list[int]], Any]

_SIZES: range = range(0, 5)
"""Sources of zero to four items: the empty one, one where every position is the head, and enough
others that a position falls before, at and after the head for some start."""

def _logical(start: int, items: ReadOnlyArray[int]) -> list[int]:
    count: int = len(items)

    return [items[(start + offset) % count] for offset in range(count)]

def _at(act: Callable[[Any, Any], Any], model: Callable[[list[int], Any], Any], argument: Any) -> tuple[_Act, _Model]:
    """One change and its model, closed over one argument: an index, a value or a count."""

    return (lambda circular: act(circular, argument), lambda items: model(items, argument))

def _chain(*steps: Callable[[Any], Any]) -> Callable[[Any], None]:
    """Several changes applied in order to one carrier, the circular list or the model."""

    def run(target: Any) -> None:
        for step in steps: step(target)

    return run

def _emptiedThenAdded(count: int) -> tuple[_Act, _Model]:
    """Every item removed, then one added: the start must come back inside a count of one."""

    return (_chain(lambda c: c.RemoveRange(0, count), lambda c: c.Add(9)), _chain(lambda l: l.clear(), lambda l: l.append(9)))

def _cases() -> Iterator[tuple[str, ReadOnlyArray[int], int, _Act, _Model]]:
    """Every structural change the circular list exposes, with the same change on the model.

    Insertions go at every logical index including the append position; removals at every
    logical index, by position and by value; and three sequences start from or return to an
    empty source, which is where the start has nowhere valid to point.
    """

    for size in _SIZES:
        items: ReadOnlyArray[int] = tuple(range(size))

        for start in range(max(size, 1)):
            for index in range(size + 1):
                yield (f"Insert({index}, 9)", items, start, *_at(lambda c, i: c.Insert(i, 9), lambda l, i: l.insert(i, 9), index))
                yield (f"TryInsert({index}, 9)", items, start, *_at(lambda c, i: c.TryInsert(i, 9), lambda l, i: l.insert(i, 9), index))
                yield (f"InsertRange({index}, [8, 9])", items, start, *_at(lambda c, i: c.InsertRange(i, [8, 9]), lambda l, i: l.__setitem__(slice(i, i), [8, 9]), index))
                yield (f"TryInsertRange({index}, [8, 9])", items, start, *_at(lambda c, i: c.TryInsertRange(i, [8, 9]), lambda l, i: l.__setitem__(slice(i, i), [8, 9]), index))

            yield ("Add(9)", items, start, lambda c: c.Add(9), lambda l: l.append(9))
            yield ("AddRange([8, 9])", items, start, lambda c: c.AddRange([8, 9]), lambda l: l.extend([8, 9]))

            for index in range(size):
                yield (f"RemoveAt({index})", items, start, *_at(lambda c, i: c.RemoveAt(i), lambda l, i: l.pop(i), index))
                yield (f"TryRemoveAt({index})", items, start, *_at(lambda c, i: c.TryRemoveAt(i), lambda l, i: l.pop(i), index))
                yield (f"RemoveRange({index}, 1)", items, start, *_at(lambda c, i: c.RemoveRange(i, 1), lambda l, i: l.pop(i), index))
                yield (f"Remove(value at {index})", items, start, *_at(lambda c, v: c.Remove(v), lambda l, v: l.remove(v), _logical(start, items)[index]))

            yield ("Add(9), then Insert(0, 7)", items, start,
                   _chain(lambda c: c.Add(9), lambda c: c.Insert(0, 7)), _chain(lambda l: l.append(9), lambda l: l.insert(0, 7)))
            yield ("Add(8), Add(9), then RemoveAt(0)", items, start,
                   _chain(lambda c: c.Add(8), lambda c: c.Add(9), lambda c: c.RemoveAt(0)), _chain(lambda l: l.extend([8, 9]), lambda l: l.pop(0)))

            if size > 0: yield ("RemoveRange(0, all), then Add(9)", items, start, *_emptiedThenAdded(size))

def _diverge(items: ReadOnlyArray[int], start: int, act: _Act, model: _Model) -> str|None:
    expected: list[int] = _logical(start, items)

    model(expected)

    circular: Any = CircularList[int](CreateList(list(items)), start)

    try: act(circular)
    except Exception as exception: return f"raised {exception!r}; the model reads {expected}"

    content: list[int] = list(circular.AsIterable())

    if content != expected: return f"reads {content}; the model reads {expected}"

    count: int = circular.GetCount()

    return None if count == 0 or 0 <= circular.GetStart() < count else f"start {circular.GetStart()} lies outside a count of {count}"

class TestTheCircularListMatchesItsModel(unittest.TestCase):
    """Every structural change, at every start and every logical index, against the model."""

    def test_every_change_matches_the_model(self) -> None:
        for label, items, start, act, model in _cases():
            with self.subTest(size = len(items), start = start, change = label):
                divergence: str|None = _diverge(items, start, act, model)

                self.assertIsNone(divergence, f"{len(items)} items, start {start}, {label}: {divergence}")

def _overEmptySizedList() -> Any:
    items: Any = TryCreateSizedList(0, list[int]())

    assert items is not None

    return CircularList[int](items, 0)

def _overEmptyOrderedSet() -> Any:
    return CircularList[int](CreateOrderedSet(list[int]()).AsList(), 0)

_EMPTY_REFUSALS: ReadOnlyArray[tuple[str, Callable[[], Any], _Act, bool|None]] = (
    ("capacity 0, TryAdd(9)",                  _overEmptySizedList,  lambda c: c.TryAdd(9),                 False),
    ("capacity 0, TryInsertRange(0, [9])",     _overEmptySizedList,  lambda c: c.TryInsertRange(0, [9]),     None),
    ("ordered set, TryAddRange([7, 7])",       _overEmptyOrderedSet, lambda c: c.TryAddRange([7, 7]),        None),
    ("ordered set, TryInsertRange(0, [7, 7])", _overEmptyOrderedSet, lambda c: c.TryInsertRange(0, [7, 7]),  None))
"""Insertions into an empty circular list over a container that refuses them. Contract.py covers
refusals on a non-empty circular list; the empty source takes a branch of its own."""

class TestAnEmptySourceAnswersAsItsContainer(unittest.TestCase):
    """D-74 on the empty branch, closed: the helper discarded the container's answer there and
    returned True, so a refused insertion into an empty circular list reported itself done."""

    def test_a_refused_insertion_answers_as_a_refusal(self) -> None:

        for label, factory, act, expected in _EMPTY_REFUSALS:
            with self.subTest(change = label):
                circular: Any = factory()

                self.assertIs(act(circular), expected, label)
                self.assertEqual(circular.GetCount(), 0, f"{label} wrote while refusing")

class TestTheModelBenchCanFail(unittest.TestCase):
    """The model bench is run against a circular list that never moves its start, which rebuilds
    D-71, D-72 and D-73 at once: green on the intact tree, red on the rebuilt one."""

    def test_it_falls_when_the_start_never_moves(self) -> None:
        def run() -> unittest.TestResult:
            result: unittest.TestResult = unittest.TestResult()

            unittest.TestSuite((TestTheCircularListMatchesItsModel("test_every_change_matches_the_model"),)).run(result)

            return result

        def frozen(self: Any, start: int = 0) -> None: pass

        intact: unittest.TestResult = run()

        self.assertEqual(len(intact.failures) + len(intact.errors), 0, "the model bench is expected to pass on the intact tree")

        target: Any = CircularList

        with mock.patch.object(target, "SetStart", frozen): broken: unittest.TestResult = run()

        self.assertGreater(len(broken.failures) + len(broken.errors), 0, "the model bench did not fall with the start frozen")
