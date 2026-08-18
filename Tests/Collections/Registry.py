"""
Regression harness for the registry and the life cycle of revocable views.

These tests are **parameterised by concrete type**: every invariant is exercised
on each indexable type that supports it, rather than on one representative.
A family assumed to be uniform has several behavioural strata, invisible to
a reading by invariant and only found by instantiating the types one by one.

Two method constraints, inherited from that review's protocol, without which the
measurements are wrong:

  * any object-lifetime measurement forces `gc.collect()` first — a view sits in
    a cycle through its own monitor updater, so its release goes through the
    cyclic collector;
  * the "mutate first, observe second" order is exercised explicitly: that is
    where the registry disarming of D-2 used to hide.

This module is not discovered by the line that runs the rest of the suite; it
has to be named:

    python3 -m unittest Tests.Collections.Registry
"""

import gc
import unittest
from typing import Any, Callable

from WinCopies.Collections.Abstraction.Collection import (
    Array, ArrayList, EquatableTuple, HashableTuple, List, SizedArray, SortedList, TryCreateSizedList, Tuple)
from WinCopies.Collections.Abstraction.Selection import List as SelectionList
from WinCopies.Collections.ObjectModel.Collection import ObservableCollection
from WinCopies.Typing.Delegate import IFunction
from WinCopies.Typing.Discard import DiscardedError

type Factory = Callable[[], Any]
type Action = Callable[[Any], Any]

class _Handle(IFunction[int]):
    """Cell initialiser for ArrayList, which takes a provider rather than a sequence."""

    def GetValue(self) -> int: return 0

def _source() -> Any: return List[int]([1, 2, 3])

def _arrayList() -> Any:
    """ArrayList initialises from a provider, so every cell starts equal. The values are
    told apart afterwards: otherwise Move and Swap would take effect without the
    observable content showing it."""

    items = ArrayList[int](3, _Handle())

    for index in range(3): items.SetAt(index, index + 1)

    return items

def _sizedArray() -> Any:
    """SizedArray fills every cell with one default value, so its cells are told apart
    afterwards for the same reason as ArrayList's."""

    items = SizedArray[int](3, 0)

    for index in range(3): items.SetAt(index, index + 1)

    return items

def _sizedList() -> Any:
    """A sized list with spare capacity: a full one refuses every insertion and would
    leave six write paths unexercised."""

    items = TryCreateSizedList(6, [1, 2, 3])

    assert items is not None

    return items

# Mutation recipes, by member name. No type carries them all; the harness exercises
# only those a type exposes, which gives C5 coverage without writing one test per
# (type, mutator) pair.
_MUTATORS: dict[str, Action] = {
    "Add":            lambda o: o.Add(9),
    "AddLeft":        lambda o: o.AddLeft(9),
    "AddRange":       lambda o: o.AddRange((7, 8)),
    "TryAddRange":    lambda o: o.TryAddRange((7, 8)),
    "Insert":         lambda o: o.Insert(1, 9),
    "TryInsert":      lambda o: o.TryInsert(1, 9),
    "InsertRange":    lambda o: o.InsertRange(1, (7, 8)),
    "TryInsertRange": lambda o: o.TryInsertRange(1, (7, 8)),
    "InsertValues":   lambda o: o.InsertValues(1, 7, 8),
    "SetAt":          lambda o: o.SetAt(0, 9),
    "TrySetAt":       lambda o: o.TrySetAt(0, 9),
    "RemoveAt":       lambda o: o.RemoveAt(0),
    "TryRemoveAt":    lambda o: o.TryRemoveAt(0),
    "Remove":         lambda o: o.Remove(1),
    "TryRemove":      lambda o: o.TryRemove(1),
    "RemoveRange":    lambda o: o.RemoveRange(0, 2),
    "TryRemoveRange": lambda o: o.TryRemoveRange(0, 2),
    "Move":           lambda o: o.Move(0, 2),
    "TryMove":        lambda o: o.TryMove(0, 2),
    "Swap":           lambda o: o.Swap(0, 2),
    "TrySwap":        lambda o: o.TrySwap(0, 2),
    "Clear":          lambda o: o.Clear(),
}

class _Case:
    """A concrete type and its factory."""

    def __init__(self, name: str, factory: Factory) -> None:
        self.name = name
        self.factory = factory

    def Create(self) -> Any: return self.factory()

class _MutableCase(_Case):
    """A mutable type, with a way to mutate it effectively and a way to be refused.

    'refuse' applies a mutation the type must reject: it is what checks C6, and its
    wording differs depending on whether the type is resizable or fixed-size.
    """

    def __init__(self, name: str, factory: Factory, mutate: Action, refuse: Action, sourced: bool = False) -> None:
        super().__init__(name, factory)

        self.mutate = mutate
        self.refuse = refuse
        self.sourced = sourced   # the type routes its registry to a source's

    def GetMutators(self, items: Any) -> list[tuple[str, Action]]:
        return [(n, f) for n, f in _MUTATORS.items() if callable(getattr(items, n, None))]

def _snapshot(items: Any) -> tuple[Any, ...]:
    """Observable content, used to establish that a mutation actually took place."""

    return tuple(items.GetAt(i) for i in range(items.GetCount()))

def _resizable(items: Any) -> Any: return items.TryRemoveAt(99)
def _fixed(items: Any) -> Any: return items.TrySetAt(99, 9)

# Abstraction stratum: own registry. ObjectModel stratum: registry routed to the
# source. The Abstract stratum is absent — its types are abstract, hence not
# instantiable; Selection has its own test class further down.
_IMMUTABLE: list[_Case] = [
    _Case("Tuple",          lambda: Tuple[int]((1, 2, 3))),
    _Case("EquatableTuple", lambda: EquatableTuple[int]((1, 2, 3))),
    _Case("HashableTuple",  lambda: HashableTuple[int]((1, 2, 3))),
]

# ObjectModel.Collection is absent on purpose: it is abstract by design, and
# ObservableCollection is its concrete type. It does instantiate at runtime, for want
# of an abstractness constraint; pyright, for its part, rejects it.
_MUTABLE: list[_MutableCase] = [
    _MutableCase("List",       lambda: List[int]([1, 2, 3]),       lambda o: o.Add(9),      _resizable),
    _MutableCase("SortedList", lambda: SortedList[int]([3, 1, 2]), lambda o: o.Add(9),      _resizable),
    _MutableCase("SizedList",  _sizedList,                         lambda o: o.SetAt(0, 9), _resizable),
    _MutableCase("Array",      lambda: Array[int]([1, 2, 3]),      lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ArrayList",  _arrayList,                         lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("SizedArray", _sizedArray,                        lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ObservableCollection", lambda: ObservableCollection[int](_source()), lambda o: o.Add(9), _resizable, True),
]
_ALL: list[_Case] = _IMMUTABLE + list(_MUTABLE)

def _revoked(view: Any) -> bool:
    try:
        view.GetCount()
        return False
    except DiscardedError:
        return True

def _countCookies() -> int:
    """Live revocation cookies. The type is private, so it is recognised by name rather
    than imported, to avoid depending on something outside the public API."""

    gc.collect()

    return sum(1 for o in gc.get_objects() if type(o).__name__ == "_RevocableViewCookie")

class TestGenerationIdentity(unittest.TestCase):
    """C2 and C3: one generation, one instance; one mutation, a fresh generation."""

    def test_same_instance_within_a_generation(self) -> None:
        for case in _ALL:
            with self.subTest(type = case.name):
                items = case.Create()

                self.assertIs(items.AsImmutable(), items.AsImmutable())

    def test_new_and_distinct_instance_after_mutation(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                first: Any = items.AsImmutable()

                case.mutate(items)

                second: Any = items.AsImmutable()

                self.assertIsNot(second, first)
                self.assertFalse(_revoked(second))

    def test_generations_chain(self) -> None:
        """Revocation is not one-shot: every generation dies in turn."""

        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                views: list[Any] = []

                for _ in range(4):
                    views.append(items.AsImmutable())

                    case.mutate(items)

                for index, view in enumerate(views):
                    with self.subTest(generation = index):
                        self.assertTrue(_revoked(view))

class TestLazyCreation(unittest.TestCase):
    """C4: no revocable is allocated until one is asked for."""

    def test_mutating_without_asking_allocates_nothing(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                before: int = _countCookies()

                for _ in range(20): case.mutate(items)

                self.assertEqual(_countCookies(), before)

class TestWritePathCoverage(unittest.TestCase):
    """C5: one test per mutator, per type. The failure mode is the forgotten path, so a
    sample proves nothing — only exhaustiveness does."""

    def test_every_mutator_revokes(self) -> None:
        """The verdict follows the effect, not the intent: a mutator that refuses need not
        revoke — that is C6 — while one that writes must."""

        for case in _MUTABLE:
            for name, mutate in case.GetMutators(case.Create()):
                with self.subTest(type = case.name, mutator = name):
                    items = case.Create()
                    view: Any = items.AsImmutable()
                    before: tuple[Any, ...] = _snapshot(items)

                    try: mutate(items)
                    except Exception as error:
                        self.skipTest(f"{name} does not apply to this type: {type(error).__name__}")

                    if _snapshot(items) == before: self.assertFalse(_revoked(view), f"{name} changed nothing yet revoked")
                    else: self.assertTrue(_revoked(view), f"{name} mutated the collection without revoking")

class TestIneffectiveMutation(unittest.TestCase):
    """C6: it is the effective mutation that revokes, not the attempt."""

    def test_a_refused_mutation_leaves_the_view_valid(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()
                before: tuple[Any, ...] = _snapshot(items)

                self.assertIsNot(case.refuse(items), True)
                self.assertEqual(_snapshot(items), before)
                self.assertFalse(_revoked(view))

class TestRootRegistration(unittest.TestCase):
    """C7 and C8: registration targets the root, and projections survive."""

    def test_mutating_the_source_revokes_a_view_taken_on_the_wrapper(self) -> None:
        source = _source()
        items = ObservableCollection[int](source)
        view: Any = items.AsImmutable()

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_a_chain_two_deep_still_reaches_the_root(self) -> None:
        source = _source()
        reversed_: Any = source.AsReversed()
        view: Any = reversed_.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_the_projection_itself_survives_the_mutation(self) -> None:
        """C8: only the revocable dies; the reversed view stays usable."""

        source = _source()
        reversed_: Any = source.AsReversed()
        view: Any = reversed_.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))
        self.assertEqual(reversed_.GetCount(), 4)

class TestRevocationIsTotal(unittest.TestCase):
    """D1: every read raises. None returns stale content."""

    def test_every_read_path_raises(self) -> None:
        for case in _MUTABLE:
            items = case.Create()
            view: Any = items.AsImmutable()

            case.mutate(items)

            reads: dict[str, Callable[[], Any]] = {
                "GetCount":  view.GetCount,
                "GetAt":     lambda: view.GetAt(0),
                "Contains":  lambda: view.Contains(1),
                "len":       lambda: len(view.AsSequence()),
                "iteration": lambda: list(view.AsIterable())}

            for name, read in reads.items():
                with self.subTest(type = case.name, read = name):
                    self.assertRaises(DiscardedError, read)

    def test_the_error_names_the_cause(self) -> None:
        """A consumer must be able to tell invalidation from disposal."""

        from WinCopies.Typing.Discard import DiscardReason, InvalidatedError

        items = List[int]([1, 2, 3])
        view: Any = items.AsImmutable()

        items.Add(9)

        with self.assertRaises(InvalidatedError) as caught: view.GetCount()

        self.assertEqual(caught.exception.GetDiscardReason(), DiscardReason.Invalidated)

class TestRepresentationDegrades(unittest.TestCase):
    """D2: ToString() and repr() do not raise — they are called once something has
    already gone wrong — and they do not leak the content."""

    def test_representation_does_not_raise_and_does_not_leak(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()

                case.mutate(items)

                for text in (view.ToString(), repr(view)):
                    self.assertIsInstance(text, str)
                    self.assertNotIn("1, 2, 3", text)

class TestSourceRelease(unittest.TestCase):
    """D5: holding on to a revoked view does not hold on to the collection."""

    def test_a_revoked_view_does_not_pin_its_source(self) -> None:
        import weakref

        items = List[int]([1, 2, 3])
        view: Any = items.AsImmutable()

        items.Add(9)

        reference = weakref.ref(items)

        del items
        gc.collect()

        self.assertTrue(_revoked(view))
        self.assertIsNone(reference())

class TestDerivedTransitivity(unittest.TestCase):
    """Addendum 3 §2.1: a derived object is built on the revocable, never on what the
    revocable wraps. Its validity is its subject's."""

    def test_a_derivative_taken_before_revocation_raises_after(self) -> None:
        for case in _MUTABLE:
            with self.subTest(type = case.name):
                items = case.Create()
                view: Any = items.AsImmutable()
                sequence = view.AsSequence()

                case.mutate(items)

                self.assertRaises(DiscardedError, lambda: len(sequence))

class TestEnumeratorInvalidation(unittest.TestCase):
    """F1': proof that the mechanism runs, not proof that it has not changed."""

    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        for case in (c for c in _MUTABLE if c.name != "ArrayList"): # see TestArrayCollectionStratum
            with self.subTest(type = case.name):
                items = case.Create()
                enumerator: Any = items.TryGetEnumerator()

                self.assertIsNotNone(enumerator)
                self.assertTrue(enumerator.MoveNext())

                case.mutate(items)

                self.assertRaises(DiscardedError, enumerator.MoveNext)

    def test_a_view_and_an_enumerator_die_on_the_same_notification(self) -> None:
        items = List[int]([1, 2, 3])
        enumerator: Any = items.TryGetEnumerator()

        enumerator.MoveNext()

        view: Any = items.AsImmutable()

        items.Add(9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)
        self.assertTrue(_revoked(view))

class TestMutateBeforeObserving(unittest.TestCase):
    """§4.4: the reverse order. That is where the registry disarming of D-2 used to hide."""

    def test_mutating_before_the_first_view_does_not_disarm_the_registry(self) -> None:
        for case in _MUTABLE:
            for count in (1, 2, 5):
                with self.subTest(type = case.name, mutationsBefore = count):
                    items = case.Create()

                    for _ in range(count): case.mutate(items)

                    view: Any = items.AsImmutable()

                    case.mutate(items)

                    self.assertTrue(_revoked(view))

class TestArrayCollectionStratum(unittest.TestCase):
    """ArrayCollection — hence ArrayList — registers its enumerators with its source's
    registry while invalidating its own. This is the D-5 residue: the view is revoked,
    the enumerator is not. Expected to fail, and marked as such rather than softened."""

    @unittest.expectedFailure
    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        items = _arrayList()
        enumerator: Any = items.TryGetEnumerator()

        enumerator.MoveNext()
        items.SetAt(0, 9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)

class TestSelectionStratum(unittest.TestCase):
    """The Selection stratum routes three of its four types to a registry of their own
    instead of their source's. This is D-8, and these tests record it — expected to
    fail, marked as such, never softened."""

    @unittest.expectedFailure
    def test_selection_list_routes_to_its_source_registry(self) -> None:
        source = _source()
        items = SelectionList[int, str](source, str, int)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    @unittest.expectedFailure
    def test_mutating_the_source_revokes_a_selection_view(self) -> None:
        source = _source()
        items = SelectionList[int, str](source, str, int)
        view: Any = items.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    @unittest.expectedFailure
    def test_mutating_the_selection_itself_revokes_its_view(self) -> None:
        items = SelectionList[int, str](_source(), str, int)
        view: Any = items.AsImmutable()

        items.Add("9")

        self.assertTrue(_revoked(view))

if __name__ == "__main__":
    unittest.main()
