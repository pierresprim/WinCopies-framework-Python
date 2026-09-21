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

This module is discovered by the line that runs the rest of the suite, and no
longer has to be named. The default unittest pattern, test*.py, matches no file
here and finds only the two packages; the suite is run with the pattern that
takes every module once:

    python3 -m unittest discover -s Tests -t . -p '[!_]*.py'
"""

import contextlib
import gc
import unittest
import weakref

from abc import abstractmethod
from collections.abc import Sequence, Generator
from typing import final, Any, Callable, cast



from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Abstraction.Collection import (
    Array, ArrayList, EquatableTuple, HashableTuple, List, SizedArray, SortedList, TryCreateSizedList, Tuple)
from WinCopies.Collections.Abstraction.Selection import (
    EquatableTuple as SelectionEquatableTuple, HashableTuple as SelectionHashableTuple, List as SelectionList)
from WinCopies.Collections.Core import ICountable, ICollection, IWriteOnlyIndexable, ITuple, IArray, IList, ISortedList
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Extensions import ITupleBase, ITuple as _ITuple, IEquatableTuple, IHashableTuple, IList as _IList, ISizedList
from WinCopies.Collections.Extensions.Revocable import RevocableViewRegistry
from WinCopies.Collections.ObjectModel.Collection import IObservableCollection, ObservableCollection
from WinCopies.Typing.Delegate import Function, Converter, IFunction
from WinCopies.Typing.Discard import DiscardReason, InvalidatedError, DiscardedError

type Factory[T] = Function[T]
type Action[T] = Converter[T, Any]

class _Handle(IFunction[int]):
    """Cell initialiser for ArrayList, which takes a provider rather than a sequence."""

    @final
    def GetValue(self) -> int: return 0

def _createTuple() -> ReadOnlyArray[int]: return (1, 2, 3)

def _equatableSource() -> IEquatableTuple[int]: return EquatableTuple[int](_createTuple())
def _hashableSource() -> IHashableTuple[int]: return HashableTuple[int](_createTuple())

def _source() -> List[int]: return List[int]([1, 2, 3])

def _arrayList() -> ArrayList[int]:
    """ArrayList initialises from a provider, so every cell starts equal. The values are
    told apart afterwards: otherwise Move and Swap would take effect without the
    observable content showing it."""

    items: ArrayList[int] = ArrayList[int](3, _Handle())

    for index in range(3): items.SetAt(index, index + 1)

    return items

def _sizedArray() -> SizedArray[int]:
    """SizedArray fills every cell with one default value, so its cells are told apart
    afterwards for the same reason as ArrayList's."""

    items: SizedArray[int] = SizedArray[int](3, 0)

    for index in range(3): items.SetAt(index, index + 1)

    return items

def _sizedList() -> ISizedList[int]:
    """A sized list with spare capacity: a full one refuses every insertion and would
    leave six write paths unexercised."""

    items: ISizedList[int]|None = TryCreateSizedList(6, [1, 2, 3])

    assert items is not None

    return items

# Mutation recipes, by member name. No type carries them all; the harness exercises
# only those a type exposes, which gives C5 coverage without writing one test per
# (type, mutator) pair.
_MUTATORS: dict[str, Action[IList[int]]] = {
    "Add":            lambda o: o.Add(9),
    "AddLeft":        lambda o: cast(ISortedList[int], o).AddLeft(9),
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

class _CaseBase:
    @abstractmethod
    def GetName(self) -> str: ...

    @abstractmethod
    def Create(self) -> Any: ...
class _Case[T](_CaseBase):
    """A concrete type and its factory."""

    def __init__(self, name: str, factory: Factory[T]) -> None:
        self.name = name
        self.factory = factory

    @final
    def GetName(self) -> str: return self.name

    def Create(self) -> T: return self.factory()

class _MutableCaseBase(_CaseBase):
    @abstractmethod
    def Mutate(self, items: IList[int]) -> object: ...
    @abstractmethod
    def Refuse(self, items: IList[int]) -> object: ...

    @abstractmethod
    def GetMutators(self, items: Any) -> ReadOnlyArray[tuple[str, Action[Any]]]: ...
class _MutableCase[T](_Case[T], _MutableCaseBase):
    """A mutable type, with a way to mutate it effectively and a way to be refused.

    'refuse' applies a mutation the type must reject: it is what checks C6, and its
    wording differs depending on whether the type is resizable or fixed-size.
    """

    def __init__(self, name: str, factory: Factory[T], mutate: Action[T], refuse: Action[T], sourced: bool = False) -> None:
        super().__init__(name, factory)

        self.__mutate: Action[T] = mutate
        self.__refuse: Action[T] = refuse
        self.sourced: bool = sourced   # the type routes its registry to a source's

    @final
    def __Process(self, items: IList[int], action: Action[T]) -> object: return action(cast(T, items))

    @final
    def Mutate(self, items: IList[int]) -> object: return self.__Process(items, self.__mutate)
    @final
    def Refuse(self, items: IList[int]) -> object: return self.__Process(items, self.__refuse)
    
    def GetMutators(self, items: T) -> ReadOnlyArray[tuple[str, Action[IList[int]]]]:
        return tuple((n, f) for n, f in _MUTATORS.items() if callable(getattr(items, n, None)))

def _snapshot(items: ITuple[int]) -> ReadOnlyArray[int]:
    """Observable content, used to establish that a mutation actually took place."""

    return tuple(items.GetAt(i) for i in range(items.GetCount()))

# Derivation forms a type may expose. Each one is a second level between the root and
# the revocable, and the failure mode C7 targets is registration with the immediate
# parent rather than the root: one level works, two levels break.
_PROJECTIONS: ReadOnlyArray[str] = ("AsReversed", "AsReadOnly", "AsFixedSize")

def _projections(items: Any) -> list[tuple[str, Any]]:
    return [(n, getattr(items, n)()) for n in _PROJECTIONS if callable(getattr(items, n, None))]

def _resizable(items: ICollection[int]) -> bool|None: return items.TryRemoveAt(99)
def _fixed(items: IWriteOnlyIndexable[int]) -> bool: return items.TrySetAt(99, 9)

# Abstraction stratum: own registry. ObjectModel stratum: registry routed to the
# source. The Abstract stratum is absent — its types are abstract, hence not
# instantiable; Selection has its own test class further down.
_IMMUTABLE: ReadOnlyArray[_CaseBase] = (
    _Case("Tuple",          lambda: Tuple[int](_createTuple())),
    _Case("EquatableTuple", lambda: _equatableSource()),
    _Case("HashableTuple",  lambda: _hashableSource()))

# ObjectModel.Collection is absent on purpose: it is abstract by design, and
# ObservableCollection is its concrete type. It does instantiate at runtime, for want
# of an abstractness constraint; pyright, for its part, rejects it.
_MUTABLE: ReadOnlyArray[_MutableCaseBase] = (
    _MutableCase("List",       _source,       lambda o: o.Add(9),      _resizable),
    _MutableCase("SortedList", lambda: SortedList[int]([3, 1, 2]), lambda o: o.Add(9),      _resizable),
    _MutableCase("SizedList",  _sizedList,                         lambda o: o.SetAt(0, 9), _resizable),
    _MutableCase("Array",      lambda: Array[int]([1, 2, 3]),      lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ArrayList",  _arrayList,                         lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("SizedArray", _sizedArray,                        lambda o: o.SetAt(0, 9), _fixed),
    _MutableCase("ObservableCollection", lambda: ObservableCollection[int](_source()), lambda o: o.Add(9), _resizable, True))

_ALL: ReadOnlyArray[_CaseBase] = _IMMUTABLE + _MUTABLE

# ArrayList is held out of three benches below, each time by an open defect. Every one of
# those exclusions has a matching expectedFailure in TestArrayCollectionStratum, so the
# defect itself is recorded — but nothing lifts the exclusion when the defect goes. A fix
# leaves it behind, and the coverage silently stays reduced without anything turning red.
# Lift each one when its named counterpart turns green.
_EXCEPT_ARRAY_LIST: ReadOnlyArray[_MutableCaseBase] = tuple(c for c in _MUTABLE if c.GetName() != "ArrayList")

def _revoked(view: ICountable) -> bool:
    try:
        view.GetCount()

        return False
    except DiscardedError: return True

def _countCookies() -> int:
    """Live revocation cookies. The type is private, so it is recognised by name rather
    than imported, to avoid depending on something outside the public API."""

    gc.collect()

    return sum(1 for o in gc.get_objects() if type(o).__name__ == "_RevocableViewCookie")

def _cookieType() -> Any:
    """The cookie type, resolved by name rather than imported: it is private, and this
    module keeps its imports to the public API."""

    import WinCopies.Collections.Extensions.Revocable as revocable

    return getattr(revocable, "_RevocableViewCookie")

@contextlib.contextmanager
def _counting() -> Generator[Function[int]]:
    """Counts the revocation cookies *constructed* inside the block.

    C4 forbids an allocation, which is a flow. A census of live cookies is a stock and
    cannot establish it: anything allocated and collected inside the window leaves the
    census unchanged. Nothing public reports a construction count, so the constructor is
    wrapped for the duration of the block and restored on the way out — the one place in
    this module that reaches past the public API, and it is confined here.
    """

    count: int = 0
    cookie: Any = _cookieType()
    original: Any = cookie.__init__

    def counted(self: Any, *args: Any, **kwargs: Any) -> None:
        nonlocal count

        count += 1

        original(self, *args, **kwargs)

    cookie.__init__ = counted

    try: yield lambda: count
    finally: cookie.__init__ = original

def _subTest(test: unittest.TestCase, case: _MutableCaseBase, action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    with test.subTest(type = case.GetName()): action(case, cast(_IList[int], case.Create()))
def __subTests(test: unittest.TestCase, cases: ReadOnlyArray[_MutableCaseBase], action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    for case in cases: _subTest(test, case, action)

def _subTests(test: unittest.TestCase, action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    __subTests(test, _MUTABLE, action)
def _arrayListSubTests(test: unittest.TestCase, action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    __subTests(test, _EXCEPT_ARRAY_LIST, action)

class TestGenerationIdentity(unittest.TestCase):
    """C2 and C3: one generation, one instance; one mutation, a fresh generation."""

    def test_same_instance_within_a_generation(self) -> None:
        for case in _ALL:
            with self.subTest(type = case.GetName()):
                items = cast(ITuple[int], case.Create())

                self.assertIs(items.AsImmutable(), items.AsImmutable())

    def test_new_and_distinct_instance_after_mutation(self) -> None:
        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            first: ITuple[int] = items.AsImmutable()
            
            case.Mutate(items)

            second: ITuple[int] = items.AsImmutable()

            self.assertIsNot(second, first)
            self.assertFalse(_revoked(second))

        _subTests(self, subTest)

    def test_generations_chain(self) -> None:
        """Revocation is not one-shot: every generation dies in turn."""

        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            views: list[ITuple[int]] = []

            for _ in range(4):
                views.append(items.AsImmutable())

                case.Mutate(items)

            for index, view in enumerate(views):
                with self.subTest(generation = index): self.assertTrue(_revoked(view))

        _subTests(self, subTest)

class TestLazyCreation(unittest.TestCase):
    """C4: no revocable is allocated until one is asked for.

    Measured as a flow, since that is what C4 states. The stock — how many cookies are
    left standing afterwards — is a different property and lives in TestRegistryRetention.
    """

    def test_mutating_without_asking_allocates_nothing(self) -> None:
        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            with _counting() as allocated:
                for _ in range(20): case.Mutate(items)

                self.assertEqual(allocated(), 0)

        _subTests(self, subTest)

    def test_the_counter_rejects_a_window_that_does_allocate(self) -> None:
        """The control at the level of the invariant: a window that violates C4 and whose
        allocations are all collected before it closes. A census returns the same figure
        for this window and for the conforming one; only the counter tells them apart, and
        that is the whole reason it is here."""

        items = _source()
        before: int = _countCookies()

        with _counting() as allocated:
            for _ in range(20):
                items.Add(9)

                view: ITuple[int] = items.AsImmutable()

                del view

            self.assertEqual(allocated(), 20)

        self.assertEqual(_countCookies(), before)

class TestRegistryRetention(unittest.TestCase):
    """D5, registry side: mutating without ever asking for a view leaves no cookie behind.

    This is what a census establishes, and it is not C4. Filed here under the invariant it
    does establish rather than under the one its previous name announced.
    """

    def test_mutating_without_asking_retains_no_cookie(self) -> None:
        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            before: int = _countCookies()

            for _ in range(20): case.Mutate(items)

            self.assertEqual(_countCookies(), before)

        _subTests(self, subTest)

class TestWritePathCoverage(unittest.TestCase):
    """C5: one test per mutator, per type. The failure mode is the forgotten path, so a
    sample proves nothing — only exhaustiveness does."""

    def test_every_mutator_revokes(self) -> None:
        """The verdict follows the effect, not the intent: a mutator that refuses need not
        revoke — that is C6 — while one that writes must."""

        for case in _MUTABLE:
            for name, mutate in case.GetMutators(case.Create()):
                with self.subTest(type = case.GetName(), mutator = name):
                    items = cast(ITupleBase[int], case.Create())
                    view = items.AsImmutable()
                    before: ReadOnlyArray[int] = _snapshot(items)

                    try: mutate(items)
                    except Exception as error: self.skipTest(f"{name} does not apply to this type: {type(error).__name__}")

                    if _snapshot(items) == before: self.assertFalse(_revoked(view), f"{name} changed nothing yet revoked")
                    else: self.assertTrue(_revoked(view), f"{name} mutated the collection without revoking")

class TestIneffectiveMutation(unittest.TestCase):
    """C6: it is the effective mutation that revokes, not the attempt."""

    def test_a_refused_mutation_leaves_the_view_valid(self) -> None:
        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            view = items.AsImmutable()
            before: ReadOnlyArray[int] = _snapshot(items)

            self.assertIsNot(case.Refuse(items), True)
            self.assertEqual(_snapshot(items), before)
            self.assertFalse(_revoked(view))

        _subTests(self, subTest)

def _project(test: unittest.TestCase, action: Callable[[_MutableCaseBase, IList[int], ITupleBase[int], ITuple[int]], None]) -> None:
    for case in _MUTABLE:
        for name, _ in _projections(case.Create()):
            with test.subTest(type = case.GetName(), projection = name):
                items: IList[int] = cast(IList[int], case.Create())
                projection: ITupleBase[int] = cast(ITupleBase[int], getattr(items, name)())

                action(case, items, projection, projection.AsImmutable())

class TestRootRegistration(unittest.TestCase):
    """C7 and C8: registration targets the root, and projections survive."""

    def test_mutating_the_source_revokes_a_view_taken_on_the_wrapper(self) -> None:
        source: _IList[int] = _source()
        items: IObservableCollection[int] = ObservableCollection[int](source)
        view: ITuple[int] = items.AsImmutable()

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_a_chain_two_deep_still_reaches_the_root(self) -> None:
        """C7 on every type and every derivation form it exposes. A revocable obtained
        from a projection must die when the root is mutated, not merely when the
        projection is."""

        def project(case: _MutableCaseBase, items: IList[int], _: ITupleBase[int], view: ITuple[int]) -> None:
            case.Mutate(items)

            self.assertTrue(_revoked(view))

        _project(self, project)

class TestProjectionsSurvive(unittest.TestCase):
    """C8: only the revocable dies. A projection is a view of the framework, not a
    dependant of the registry; invalidating it too would change the behaviour of a
    pre-existing type for reasons unrelated to immutability."""

    def test_the_projection_itself_survives_the_mutation(self) -> None:
        def project(case: _MutableCaseBase, items: IList[int], projection: ITupleBase[int], view: ITuple[int]) -> None:
            expected: int = items.GetCount()

            case.Mutate(items)

            self.assertTrue(_revoked(view))
            self.assertEqual(projection.GetCount(), items.GetCount())
            self.assertGreaterEqual(items.GetCount(), min(expected, 1))

        _project(self, project)

class TestRevocationIsTotal(unittest.TestCase):
    """D1: every read raises. None returns stale content.

    Totality is not reached today: ==, != and hash() answer on a revoked view. They are
    left out of the sweep below and recorded in TestEqualityContract instead, so that the
    hole reads as a known defect rather than as a claim of totality that happens to pass.
    """

    def test_every_read_path_raises(self) -> None:
        for case in _MUTABLE:
            items: _IList[int] = cast(_IList[int], case.Create())
            view: _ITuple[int] = items.AsImmutable()

            case.Mutate(items)

            reads: dict[str, Function[Any]] = {
                "GetCount":  view.GetCount,
                "GetAt":     lambda: view.GetAt(0),
                "Contains":  lambda: view.Contains(1),
                "len":       lambda: len(view.AsSequence()),
                "iteration": lambda: list(view.AsIterable())}

            for name, read in reads.items():
                with self.subTest(type = case.GetName(), read = name): self.assertRaises(DiscardedError, read)

    def test_the_error_names_the_cause(self) -> None:
        """A consumer must be able to tell invalidation from disposal."""

        items: IList[int] = _source()
        view: ITuple[int] = items.AsImmutable()

        items.Add(9)

        with self.assertRaises(InvalidatedError) as caught: view.GetCount()

        self.assertEqual(caught.exception.GetDiscardReason(), DiscardReason.Invalidated)

class TestEqualityContract(unittest.TestCase):
    """B4 files Equals under content reading, alongside Contains and Count: a revocable
    must expose it, and must raise once revoked. It does neither. And one view type serves
    every subject, so what the subject decided about equality is neither carried nor
    withheld faithfully.

    D-31 and D-32, recorded here so that a fix has something to turn green. Without these
    the two defects would live in a report and nowhere else.
    """

    @unittest.expectedFailure
    def test_equality_raises_on_a_revoked_view(self) -> None:
        """D-31: fifteen read paths raise, == and != answer as though nothing happened."""

        items: IList[int] = _source()
        view: ITuple[int] = items.AsImmutable()
        other: ITuple[int] = _source().AsImmutable()

        items.Add(9)

        self.assertRaises(DiscardedError, lambda: view == other)

    @unittest.expectedFailure
    def test_hashing_raises_on_a_revoked_view(self) -> None:
        """D-31, second half: a revoked view still answers hash()."""

        items: IList[int] = _source()
        view: ITuple[int] = items.AsImmutable()

        items.Add(9)

        self.assertRaises(DiscardedError, lambda: hash(view))

    @unittest.expectedFailure
    def test_a_view_carries_the_equality_of_its_subject(self) -> None:
        """D-32: the subject compares by content, its view by identity, so AsImmutable()
        returns something that is not substitutable for what it exposes."""

        subject: IEquatableTuple[int] = _equatableSource()
        other: IEquatableTuple[int] = _equatableSource()

        self.assertTrue(subject.Equals(other))
        self.assertEqual(subject.AsImmutable(), other.AsImmutable())

    @unittest.expectedFailure
    def test_a_view_does_not_grant_a_hashability_its_subject_refuses(self) -> None:
        """D-32, the other way round: EquatableTuple is deliberately unhashable, and its own
        view hands out object.__hash__. A type that cannot be a key has a view that can."""

        subject: IEquatableTuple[int] = _equatableSource()

        self.assertRaises(TypeError, lambda: hash(subject))
        self.assertRaises(TypeError, lambda: hash(subject.AsImmutable()))

class TestRepresentationDegrades(unittest.TestCase):
    """D2: ToString() and repr() do not raise — they are called once something has
    already gone wrong — and they do not leak the content."""

    def test_representation_does_not_raise_and_does_not_leak(self) -> None:
        """Both contents are checked for, and neither is spelled out.

        Looking for one literal string misses whichever type no longer contains it: on the
        four types whose witness mutation is SetAt(0, 9), the content stops being 1, 2, 3
        and the assertion cannot bite. A leak has two shapes anyway — handing out the
        snapshot the view was given, or reading through to what the collection now holds —
        so both are built from the collection itself.
        """

        def subTest(case: _MutableCaseBase, items: _IList[int]) -> None:
            before: ReadOnlyArray[int] = _snapshot(items)
            view: _ITuple[int] = items.AsImmutable()

            case.Mutate(items)

            contents: ReadOnlyArray[str] = tuple(", ".join(str(value) for value in content)
                                                    for content in (before, _snapshot(items)) if content)

            for text in (view.ToString(), repr(view)):
                self.assertIsInstance(text, str)

                for content in contents:
                    with self.subTest(content = content): self.assertNotIn(content, text)

        _subTests(self, subTest)

class TestSourceRelease(unittest.TestCase):
    """D5: holding on to a revoked view does not hold on to the collection."""

    def test_a_revoked_view_does_not_pin_its_source(self) -> None:
        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            view = items.AsImmutable()

            case.Mutate(items)

            reference = weakref.ref(items)

            del items
            gc.collect()   # the view sits in a cycle: refcounting alone never frees it

            self.assertTrue(_revoked(view))
            self.assertIsNone(reference())

        _subTests(self, subTest)

class TestDerivedTransitivity(unittest.TestCase):
    """Addendum 3 §2.1, perimeter settled by the reformulated B4: transitivity applies to
    what reads through the revocable, not to what materialises from it nor to what
    consumes it over time.

    A view — AsSequence(), AsReversed() — is built on the revocable and dies with it. A
    slice is a snapshot taken at the call, so one obtained while the revocable was alive
    legitimately survives; but obtaining one is a data access, so the call itself must
    raise once the revocable is dead. Cursors are a category of their own and are
    covered by TestCursorContract.
    """

    def test_a_view_taken_before_revocation_raises_after(self) -> None:
        reads: dict[str, Converter[object, int]] = {
            "AsSequence": lambda derived: len(cast(Sequence[int], derived)),
            "AsReversed": lambda derived: cast(ITuple[int], derived).GetCount()}

        for case in _MUTABLE:
            for name, read in reads.items():
                with self.subTest(type = case.GetName(), derivative = name):
                    items = cast(IList[int], case.Create())
                    view = items.AsImmutable()
                    derived = getattr(view, name)()

                    self.assertIsNotNone(derived)

                    case.Mutate(items)

                    self.assertRaises(DiscardedError, lambda: read(derived))

    def test_taking_a_slice_after_revocation_raises(self) -> None:
        """Obtaining a slice is a data access, so it falls under D1."""

        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            view: ITuple[int] = items.AsImmutable()
            
            case.Mutate(items)

            self.assertRaises(DiscardedError, lambda: view.SliceAt(slice(0, 2)))

        _subTests(self, subTest)

    def test_a_slice_taken_before_revocation_is_a_snapshot(self) -> None:
        """A slice is an independent collection, so one obtained while the revocable was
        alive keeps the content it was given."""

        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            view: ITuple[int] = items.AsImmutable()
            taken = view.SliceAt(slice(0, 2))
            expected: ReadOnlyArray[int] = _snapshot(taken)

            case.Mutate(items)

            self.assertEqual(_snapshot(taken), expected)

        # Lift with TestArrayCollectionStratum.test_a_slice_is_an_independent_collection.
        _arrayListSubTests(self, subTest)

def _assertIsNotNone[T](case: unittest.TestCase, value: T|None) -> T:
    case.assertIsNotNone(value)

    assert value is not None

    return value

class TestCursorContract(unittest.TestCase):
    """Reformulated B4: TryGetEnumerator() returns a cursor, not a view. A cursor consumes
    a sequence over time instead of exposing a content, so it is not subject to
    transitivity: it is anchored on the source and invalidated straight by the registry.

    Two consequences, both asserted below. A cursor may outlive the revocable that
    produced it, and it may not outlive a mutation of the source. The first needs a
    revocation that does not mutate the source, which no collection path offers: a
    registry of its own supplies it.
    """

    def test_a_cursor_outlives_the_revocable_that_produced_it(self) -> None:
        """The half of the rule that a collection cannot show. Reached through a collection,
        the revocation of the view and the death of the cursor have one and the same cause —
        the source mutation — so no bench built that way can tell survival from coincidence.
        A registry of its own is invalidated directly instead: the view dies, the source is
        never touched, and the cursor must go on."""

        registry: RevocableViewRegistry = RevocableViewRegistry()
        items: _IList[int] = _source()
        view: _ITuple[int] = registry.CreateRevocableView(items.AsReadOnly())
        cursor: IEnumerator[int] = _assertIsNotNone(self, view.TryGetEnumerator())

        self.assertTrue(cursor.MoveNext())

        registry.InvalidateObjects()

        self.assertTrue(_revoked(view))
        self.assertTrue(cursor.MoveNext())              # the view does not carry the cursor away
        self.assertEqual(cursor.GetCurrent(), 2)
        self.assertEqual(_snapshot(items), _createTuple())   # and the source is untouched

    def test_a_cursor_is_anchored_on_the_source_and_not_on_the_view(self) -> None:
        """Telling the two anchorings apart needs a view whose revocation is decoupled from
        its source's mutations: only then does an anchoring on the view show as survival
        where an anchoring on the source shows as death.

        D-8 supplies such a view by accident — Selection.List is revoked by nothing — and
        the bench first built here rested on it, so the step 4 fix would have turned this
        test red with nothing to announce it. A registry of its own supplies the same
        configuration by construction: the view is registered with that registry, which the
        collection never notifies."""

        registry: RevocableViewRegistry = RevocableViewRegistry()
        items: _IList[int] = _source()
        view: _ITuple[int] = registry.CreateRevocableView(items.AsReadOnly())
        cursor = _assertIsNotNone(self, view.TryGetEnumerator())

        self.assertTrue(cursor.MoveNext())

        items.Add(9)

        self.assertFalse(_revoked(view))                    # decoupled by construction, not by defect
        self.assertRaises(DiscardedError, cursor.MoveNext)  # the cursor follows the source all the same

    def test_a_cursor_does_not_outlive_a_mutation_of_the_source(self) -> None:
        # Lift with TestArrayCollectionStratum.test_a_cursor_obtained_through_a_view_dies_on_mutation.
            def subTest(case: _MutableCaseBase, items: _IList[int]) -> None:
                view: _ITuple[int] = items.AsImmutable()
                cursor: IEnumerator[int] = _assertIsNotNone(self, view.TryGetEnumerator())

                self.assertTrue(cursor.MoveNext())

                case.Mutate(items)

                self.assertRaises(DiscardedError, cursor.MoveNext)

            _arrayListSubTests(self, subTest)

class TestEnumeratorInvalidation(unittest.TestCase):
    """F1': proof that the mechanism runs, not proof that it has not changed."""

    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        # Lift with TestArrayCollectionStratum.test_an_active_enumerator_dies_on_mutation.
            def subTest(case: _MutableCaseBase, items: _IList[int]) -> None:
                enumerator: IEnumerator[int] = _assertIsNotNone(self, items.TryGetEnumerator())

                self.assertTrue(enumerator.MoveNext())

                case.Mutate(items)

                self.assertRaises(DiscardedError, enumerator.MoveNext)

            _arrayListSubTests(self, subTest)

    def test_a_view_and_an_enumerator_die_on_the_same_notification(self) -> None:
        items: _IList[int] = _source()
        enumerator: IEnumerator[int] = _assertIsNotNone(self, items.TryGetEnumerator())

        enumerator.MoveNext()

        view: ITuple[int] = items.AsImmutable()

        items.Add(9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)
        self.assertTrue(_revoked(view))

class TestMutateBeforeObserving(unittest.TestCase):
    """§4.4: the reverse order. That is where the registry disarming of D-2 used to hide."""

    def test_mutating_before_the_first_view_does_not_disarm_the_registry(self) -> None:
        for case in _MUTABLE:
            for count in (1, 2, 5):
                with self.subTest(type = case.GetName(), mutationsBefore = count):
                    items: IList[int] = cast(IList[int], case.Create())

                    for _ in range(count): case.Mutate(items)

                    view: ITuple[int] = items.AsImmutable()

                    case.Mutate(items)

                    self.assertTrue(_revoked(view))

class TestArrayCollectionStratum(unittest.TestCase):
    """ArrayCollection — hence ArrayList — registers its enumerators with its source's
    registry while invalidating its own. This is the D-5 residue: the view is revoked,
    the enumerator is not. Expected to fail, and marked as such rather than softened."""

    @unittest.expectedFailure
    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        items: ArrayList[int] = _arrayList()
        enumerator: IEnumerator[int] = _assertIsNotNone(self, items.TryGetEnumerator())

        enumerator.MoveNext()
        items.SetAt(0, 9)

        self.assertRaises(DiscardedError, enumerator.MoveNext)

    @unittest.expectedFailure
    def test_a_cursor_obtained_through_a_view_dies_on_mutation(self) -> None:
        """Same cause, second path: a cursor must not outlive a mutation of its source, and
        this one does whether it was obtained from the collection or through a view."""

        items: ArrayList[int] = _arrayList()
        view: _ITuple[int] = items.AsImmutable()
        cursor: IEnumerator[int] = _assertIsNotNone(self, view.TryGetEnumerator())

        items.SetAt(0, 9)

        self.assertRaises(DiscardedError, cursor.MoveNext)

    @unittest.expectedFailure
    def test_a_slice_is_an_independent_collection(self) -> None:
        """ArrayCollection holds an array of cells rather than of values, and its slice
        copies the list of cells rather than the cells: parent and slice share the very
        same boxes, and writing through either is visible from the other. Every other
        indexable type returns a snapshot.

        This is not recorded as a defect. Holding references rather than values is what
        the type is for, so sharing them may well be the intent; whether a slice should
        copy the boxes is a design question, pending arbitration. The test states the
        rule the rest of the family follows, and will turn green on its own should the
        arbitration go that way.
        """

        items: ArrayList[int] = _arrayList()
        taken: IArray[int] = items.SliceAt(slice(0, 2))
        expected: ReadOnlyArray[int] = _snapshot(taken)

        items.SetAt(0, 9)

        self.assertEqual(_snapshot(taken), expected)

class TestSelectionStratum(unittest.TestCase):
    """The Selection stratum routes three of its four types to a registry of their own
    instead of their source's. This is D-8, and these tests record it — expected to
    fail, marked as such, never softened.

    Two of the three carry a third status. Their defect is established structurally —
    the registries measurably differ — but cannot be exercised behaviourally, because
    their source is immutable and no mutation can therefore revoke anything. Those are
    skipped with a reason that names the defect, so that it stays visible in the report
    without inflating the failure count. A skip here is a finding, not an omission.
    """

    @unittest.expectedFailure
    def test_selection_list_routes_to_its_source_registry(self) -> None:
        source: _IList[int] = _source()
        items: _IList[str] = SelectionList[int, str](source, str, int)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    @unittest.expectedFailure
    def test_selection_equatable_tuple_routes_to_its_source_registry(self) -> None:
        """Structural half of the defect for the immutable-sourced types: exerciseable,
        and failing."""

        source: IEquatableTuple[int] = _equatableSource()
        items: IEquatableTuple[str] = SelectionEquatableTuple[int, str](source, str)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    @unittest.expectedFailure
    def test_selection_hashable_tuple_routes_to_its_source_registry(self) -> None:
        source: IHashableTuple[int] = _hashableSource()
        items: IHashableTuple[str] = SelectionHashableTuple[int, str](source, str)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_selection_tuples_cannot_be_exercised_behaviourally(self) -> None:
        """Behavioural half: not exerciseable. Recorded rather than silently dropped."""

        self.skipTest("D-8, third status: Selection.EquatableTuple and Selection.HashableTuple keep a "
                      "registry of their own — measured by test_selection_equatable_tuple_routes_to_its_source_registry — "
                      "but their source is immutable, so no mutation can revoke a view and the consequence "
                      "cannot be exercised. Defect established, not exerciseable.")

    @unittest.expectedFailure
    def test_mutating_the_source_revokes_a_selection_view(self) -> None:
        source: _IList[int] = _source()
        items: IList[str] = SelectionList[int, str](source, str, int)
        view: ITuple[str] = items.AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    @unittest.expectedFailure
    def test_mutating_the_selection_itself_revokes_its_view(self) -> None:
        items: IList[str] = SelectionList[int, str](_source(), str, int)
        view: ITuple[str] = items.AsImmutable()

        items.Add("9")

        self.assertTrue(_revoked(view))

if __name__ == "__main__":
    unittest.main()
