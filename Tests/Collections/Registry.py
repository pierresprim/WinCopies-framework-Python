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
from WinCopies.Collections.Abstraction.Collection import (Tuple, EquatableTuple, HashableTuple,
                                                          Array, ArrayList, SizedArray,
                                                          List, SortedList,
                                                          TryCreateSizedList)
from WinCopies.Collections.Abstract.Collection import Tuple as ConvertingTuple, List as ConvertingList
from WinCopies.Collections.Abstraction.Mapping.Extensions import CreateOrderedSet
from WinCopies.Collections.Abstraction.Selection import (Converters,
                                                         EquatableTuple as SelectionEquatableTuple, HashableTuple as SelectionHashableTuple,
                                                         List as SelectionList)
from WinCopies.Collections.Core import Mutability, ICountable, ICollection, IWriteOnlyIndexable, ITuple, IArray, IList, ISortedList
from WinCopies.Collections.Enumeration import IterationResult
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Extensions import IDefaultMutableSequence, ITupleBase, ITuple as _ITuple, ISortedTuple, IEquatableTuple, IHashableTuple, IList as _IList, ISizedList
from WinCopies.Collections.Extensions.Revocable import RevocableViewRegistry
from WinCopies.Collections.ObjectModel.Collection import IObservableCollection, ObservableCollection
from WinCopies.Typing import InvalidOperationError
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

def _snapshot[T](items: ITuple[T]) -> ReadOnlyArray[T]:
    """Observable content, used to establish that a mutation actually took place.

    Generic over the element type: the selection stratum converts, so its benches read
    a tuple of str out of a source of int.
    """

    return tuple(items.GetAt(i) for i in range(items.GetCount()))

# Converting collections: TIn inside, TOut outside. S10 asks for the registration to reach
# the root across a conversion, which no projection form exercises — a converter is the one
# derivation that changes the element type rather than the order or the write surface.
class _ConvertingTuple(ConvertingTuple[int, str]):
    """Read-only converter over an inner tuple of ints."""

    def _Clone(self, items: Any) -> "_ConvertingTuple": return _ConvertingTuple(items)

    def _Convert(self, item: int) -> str: return str(item)

    def GetMutability(self) -> Mutability: return Mutability.ReadOnly
# The opt-in is the consumer's, not the template's: Abstract.Collection.List leaves
# _Reverse abstract so that each subclass decides what a reversal means for it, exactly
# as the framework's own Selection.List opts in rather than inheriting a decision. A
# converter reorders without converting, so the pairwise default is right here -- and it
# is what this double did before the hook existed.
class _ConvertingList(ConvertingList[int, str], IDefaultMutableSequence[str]):
    """Two-way converter over an inner list of ints."""

    def _Clone(self, items: Any) -> "_ConvertingList": return _ConvertingList(items)

    def _Convert(self, item: int) -> str: return str(item)
    def _ConvertBack(self, item: str) -> int: return int(item)

    def GetMutability(self) -> Mutability: return Mutability.Mutable

# Depth at which the generation chain is attested. Addendum 5 §1 records fifty, measured
# out of tree; the figure is carried here so that the claim and its check are the same
# object.
_GENERATIONS: int = 50

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
def _subTestsOf(test: unittest.TestCase, cases: ReadOnlyArray[_MutableCaseBase], action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    for case in cases: _subTest(test, case, action)

# Every mutable case. Three benches once ran on _MUTABLE minus ArrayList, one open defect
# each, and each exclusion was paired with a named bench on that type: the named counterpart
# signals by turning into an unexpected success, an exclusion by name signals nothing and has
# to be lifted by hand. The three defects are closed, the exclusions and their counterparts
# are both gone, and no subset by name is left. The one subset that remains, below, is
# computed from what the types expose and its complement is asserted by a bench of its own —
# which is what makes it a fact about the family rather than the marker of an open defect.
def _subTests(test: unittest.TestCase, action: Callable[[_MutableCaseBase, _IList[int]], None]) -> None:
    _subTestsOf(test, _MUTABLE, action)

def _writableSlices() -> ReadOnlyArray[_MutableCaseBase]:
    """The cases whose slice offers a positional write, measured rather than listed: a type
    that gains or loses one is picked up here without anything to edit. The complement is
    asserted by TestSliceIndependence.test_one_type_alone_slices_without_a_write_surface."""

    return tuple(case for case in _MUTABLE if isinstance(case.Create().SliceAt(slice(0, 2)), IArray))

# The equatable and hashable subjects, enumerated by family. AsImmutable() promises a
# narrowed return type per family, and the unit of that promise is the family and not one
# representative: of the five equatable paths below, three miss it and two keep it, and no
# single representative would have shown both.
def _equatableSubjects() -> ReadOnlyArray[_CaseBase]:
    """Every constructible IEquatableTuple.

    The reversed form of the ordered-set tuple is absent, and cannot be added: its
    AsReversed() recurses without terminating — a defect older than this bench, reported on
    its own. Listing it here would hang the suite rather than fail it.
    """

    return (
        _Case("EquatableTuple",                     _equatableSource),
        _Case("EquatableTuple.AsReversed",          lambda: _equatableSource().AsReversed()),
        _Case("SelectionEquatableTuple",            lambda: SelectionEquatableTuple[int, str](_equatableSource(), str)),
        _Case("SelectionEquatableTuple.AsReversed", lambda: SelectionEquatableTuple[int, str](_equatableSource(), str).AsReversed()),
        _Case("OrderedSetTuple",                    lambda: CreateOrderedSet(_createTuple()).AsTuple()))

def _hashableSubjects() -> ReadOnlyArray[_CaseBase]:
    """Every constructible IHashableTuple, reversed and converting forms included."""

    return (
        _Case("HashableTuple",                     _hashableSource),
        _Case("HashableTuple.AsReversed",          lambda: _hashableSource().AsReversed()),
        _Case("SelectionHashableTuple",            lambda: SelectionHashableTuple[int, str](_hashableSource(), str)),
        _Case("SelectionHashableTuple.AsReversed", lambda: SelectionHashableTuple[int, str](_hashableSource(), str).AsReversed()))

def _allocatesAView(subject: _ITuple[Any]) -> bool:
    """Whether AsImmutable() went through the revocable registry, read as a flow of cookie
    constructions and not as a census — the distinction _counting exists for. Takes a fresh
    subject each time, since a view is memoised after its first request."""

    with _counting() as count: subject.AsImmutable()

    return count() > 0

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

    def test_the_chain_holds_at_fifty_generations(self) -> None:
        """The depth the dossier attests, brought into the repository.

        `test_generations_chain` establishes the shape on four generations, which is what
        T1 asks; the fifty of addendum 5 §1 were measured once, out of tree, and nothing
        in the harness said at what depth the chain still held. Depth is the axis on which
        a latch degrades without the shape changing — D-2 was exactly a two-position latch
        that looked right for one generation — so it is worth asserting rather than
        remembering.

        One type is enough here: the shape is already covered on every type above, and
        what this bench adds is depth, not breadth.
        """

        items: IList[int] = _source()
        views: list[ITuple[int]] = []

        for _ in range(_GENERATIONS):
            views.append(items.AsImmutable())

            items.Add(9)

        self.assertEqual(len(views), _GENERATIONS)

        revoked: int = sum(1 for view in views if _revoked(view))

        self.assertEqual(revoked, _GENERATIONS, f"{revoked} of {_GENERATIONS} generations were revoked")

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

# The value the containment and search paths look for. Named rather than written twice: the
# bench compares what a path returns against what the content says it should, and the two
# sides have to be asking the same question for the comparison to mean anything.
_PROBE_VALUE: int = 1

def _readPaths(view: _ITuple[int]) -> dict[str, Function[Any]]:
    """The read surface D1 speaks of, shared by the two benches below.

    They are two halves of one statement: these paths answer while the view is alive, and
    they raise once it is revoked. Asserting only the second half would pass just as well
    on a path that never answers at all.

    The Python protocol surface is swept alongside the named one, and for the same reason it
    exists: a consumer reaches a view through len(), iteration and indexing without thinking
    about it, so a hole there would be the one nobody notices. An adversarial sweep of a
    revoked view found none — every path below refuses — but the finding deserves an assertion
    rather than a note, since one point of passage holds them all and a refactoring moves
    points of passage.

    Those paths go through AsSequence(), which is measured to be the view itself, so the
    object and the methods are the same ones a consumer reaches with len() or a subscript.
    What changes is the typing: ITuple does not statically promise Sized, Iterable, indexable
    or Reversible, and both checkers say so on the direct form. Reaching the surface through
    the API that declares it costs nothing at runtime and keeps the sweep type-clean.
    """

    return {"GetCount":       view.GetCount,
            "GetAt":          lambda: view.GetAt(0),
            "Contains":       lambda: view.Contains(_PROBE_VALUE),
            "TryGetValue":    lambda: view.TryGetValue(0).GetValue(),
            "FindFirstIndex": lambda: view.FindFirstIndex(_PROBE_VALUE),
            "len":            lambda: len(view.AsSequence()),
            "iteration":      lambda: list(view.AsIterable()),
            "getitem":        lambda: view.AsSequence()[0],
            "slice":          lambda: list(view.AsSequence()[0:2]),
            "in":             lambda: _PROBE_VALUE in view.AsSequence(),
            "reversed()":     lambda: list(reversed(view.AsSequence())),
            "bool()":         lambda: bool(view.AsSequence())}

class TestRevocationIsTotal(unittest.TestCase):
    """D1: every read raises. None returns stale content.

    Totality is not reached today: ==, != and hash() answer on a revoked view. They are
    left out of the sweep below and recorded in TestEqualityContract instead, so that the
    hole reads as a known defect rather than as a claim of totality that happens to pass.
    """

    def test_every_read_path_answers_before_revocation(self) -> None:
        """The control the bench below needs in order to mean anything.

        `test_every_read_path_raises` is satisfied by a path that raises for the wrong
        reason, or that cannot answer at all. D-33 was exactly that: `Contains` recursed
        without bound on ArrayList, and the sweep never saw it because it only ever ran
        against a revoked view, where revocation raised first. A read path has to be shown
        working before its refusal proves anything.

        The values are checked, not merely the absence of an exception: a path that
        answers wrongly would otherwise read as healthy.
        """

        expected: dict[str, Callable[[ReadOnlyArray[int]], Any]] = {
            "GetCount":       lambda content: len(content),
            "GetAt":          lambda content: content[0],
            "Contains":       lambda content: _PROBE_VALUE in content,
            "TryGetValue":    lambda content: content[0],
            "FindFirstIndex": lambda content: content.index(_PROBE_VALUE),
            "len":            lambda content: len(content),
            "iteration":      lambda content: list(content),
            "getitem":        lambda content: content[0],
            "slice":          lambda content: list(content[0:2]),
            "in":             lambda content: _PROBE_VALUE in content,
            "reversed()":     lambda content: list(reversed(content)),
            "bool()":         lambda content: bool(content)}

        for case in _ALL:
            items = cast(_ITuple[int], case.Create())
            content: ReadOnlyArray[int] = _snapshot(items)
            view: _ITuple[int] = items.AsImmutable()

            for name, read in _readPaths(view).items():
                with self.subTest(type = case.GetName(), read = name):
                    self.assertEqual(read(), expected[name](content))

    def test_a_read_path_reports_an_absent_value_as_absent(self) -> None:
        """The other half of D-33's lesson, and the more dangerous one.

        The correction that suggests itself for a containment test is to delegate to the
        inner container, which on the array strata holds boxes rather than values: it
        answers False for everything, present or not. That trades a loud failure for a
        silent wrong answer, so the absent case is asserted alongside the present one.
        """

        for case in _ALL:
            items = cast(_ITuple[int], case.Create())
            absent: int = max(_snapshot(items)) + 1
            view: _ITuple[int] = items.AsImmutable()

            with self.subTest(type = case.GetName()):
                self.assertTrue(view.Contains(_snapshot(items)[0]))
                self.assertFalse(view.Contains(absent))

    def test_every_read_path_raises(self) -> None:
        for case in _MUTABLE:
            items: _IList[int] = cast(_IList[int], case.Create())
            view: _ITuple[int] = items.AsImmutable()

            case.Mutate(items)

            for name, read in _readPaths(view).items():
                with self.subTest(type = case.GetName(), read = name): self.assertRaises(DiscardedError, read)

    def test_the_error_names_the_cause(self) -> None:
        """A consumer must be able to tell invalidation from disposal."""

        items: IList[int] = _source()
        view: ITuple[int] = items.AsImmutable()

        items.Add(9)

        with self.assertRaises(InvalidatedError) as caught: view.GetCount()

        self.assertEqual(caught.exception.GetDiscardReason(), DiscardReason.Invalidated)

def _revocableEquatableView() -> tuple[IEquatableTuple[int], Action[Any]]:
    """An equatable view that can actually be revoked, with the mutation that revokes it.

    The ordered set's tuple is the only equatable subject in reach whose source is mutable:
    EquatableTuple and HashableTuple are both ReadOnly over a ReadOnly source, so their views
    are never revoked and could not carry a bench about revocation at all.
    """

    items = CreateOrderedSet(_createTuple())

    return (items.AsTuple().AsImmutable(), lambda _: items.Add(9))

class TestEqualityContract(unittest.TestCase):
    """D-31 and D-32, and what became of them.

    D-32 is closed. A view used to compare by identity where its subject compared by content,
    and to hand out object.__hash__ where its subject refused to be hashed — one view class
    served every subject, so what the subject decided was neither carried nor withheld
    faithfully. Two concrete view classes closed both halves, and the two benches that
    recorded them are now ordinary green benches.

    D-31 is closed for the equatable family and deliberately open for the plain one. An
    equatable view refuses equality once revoked, because its Equals goes through the same
    guard as every other read. A plain view has no equality of its own: it falls back to
    object, which compares by identity and hashes by address, and neither touches the guard.
    That is an exclusion by omission, not by choice — the design rule gives a plain view no
    equality to refuse — so the second bench asserts the exclusion rather than wishing it
    away. It turns red the day a plain view acquires an equality, which is when the question
    would need answering again.

    The symmetrical bench on hashing is absent on purpose: an equatable view is unhashable
    before revocation as well as after, so "hashing raises once revoked" would pass without
    measuring revocation at all. Measured, not assumed.
    """

    def test_a_revoked_equatable_view_refuses_equality(self) -> None:
        """D-31 for the family that has an equality to refuse.

        Both halves are asserted. A bench that only checks the refusal passes just as well on
        a view whose equality never answered in the first place — the lesson of D-33, applied
        here to the one read path the revocation sweep cannot reach, since it lives on the
        type rather than on the guard.
        """

        view, revoke = _revocableEquatableView()
        other, _ = _revocableEquatableView()

        self.assertEqual(view, other)

        revoke(None)

        self.assertRaises(DiscardedError, lambda: view == other)
        self.assertRaises(DiscardedError, lambda: view.Equals(other))

    def test_a_plain_view_is_excluded_from_the_equality_contract(self) -> None:
        """The exclusion, asserted rather than wished away — the counterpart of the bench
        above and the record of what D-31 leaves open.

        A plain view inherits object's equality and hashing, so a revoked one still answers
        both: identity remains well defined once the content is gone. These assertions are
        what makes the omission visible, and what turns red the day a plain view is given an
        equality of its own — at which point it owes the refusal too.
        """

        items: IList[int] = _source()
        view: ITuple[int] = items.AsImmutable()
        other: ITuple[int] = _source().AsImmutable()

        items.Add(9)

        self.assertTrue(_revoked(view), "the view must be revoked here, or the two assertions below mean nothing")
        self.assertFalse(view == other)
        self.assertIsInstance(hash(view), int)

    def test_a_view_carries_the_equality_of_its_subject(self) -> None:
        """D-32: the subject compares by content, and so must its view, or AsImmutable()
        returns something that is not substitutable for what it exposes. Was an expected
        failure while one view class served every subject."""

        subject: IEquatableTuple[int] = _equatableSource()
        other: IEquatableTuple[int] = _equatableSource()

        self.assertTrue(subject.Equals(other))
        self.assertEqual(subject.AsImmutable(), other.AsImmutable())

    def test_a_view_does_not_grant_a_hashability_its_subject_refuses(self) -> None:
        """D-32, the other way round: EquatableTuple is deliberately unhashable, so a type
        that cannot be a key must not have a view that can."""

        subject: IEquatableTuple[int] = _equatableSource()

        self.assertRaises(TypeError, lambda: hash(subject))
        self.assertRaises(TypeError, lambda: hash(subject.AsImmutable()))

class TestImmutableViewTyping(unittest.TestCase):
    """AsImmutable() promises a narrowed return type per family, and the promise is now kept.

    It was not when this class was written. The revocable view had a single concrete class, so
    the narrowed overloads of CreateRevocableView could not be honoured whatever they
    declared, and neither checker saw it: on a minimal probe of the same shape — overloads
    from narrowest to widest, an implementation returning the union and constructing only the
    widest class — pyright 1.1.414 and mypy 2.3.1, both strict, reported nothing. Nothing in
    the suite read the returned type either, which is how a green suite sat on top of it.

    Two concrete views and a runtime dispatch closed it. The benches are kept as they are: the
    promise is held by a class choice made at one point in the code, and a class choice is
    exactly what a refactoring moves without noticing.

    The hashable family is held differently — by construction rather than by care.
    IHashableTuple declares AsImmutable @final and answers with itself, so there is no view to
    be wrong about, and the overload that once promised one is gone. While an override of that
    @final stood, the hashable path through Selection returned a revocable view under an
    IHashableTuple signature; the first two benches keep that from coming back.
    """

    def test_a_hashable_subject_is_its_own_immutable_view(self) -> None:
        """A hashable tuple cannot mutate — it is part of the contract — so it is already its
        own immutable view. Four paths, the two the removed override went through included."""

        for case in _hashableSubjects():
            with self.subTest(type = case.GetName()):
                subject: IHashableTuple[Any] = case.Create()

                self.assertIs(subject.AsImmutable(), subject)

    def test_a_hashable_subject_allocates_no_view(self) -> None:
        """The same contract read as a cost instead of a type. An override returning something
        of the right type but allocating to get there would pass the bench above and fall
        here, which is why both are kept."""

        for case in _hashableSubjects():
            with self.subTest(type = case.GetName()):
                self.assertFalse(_allocatesAView(case.Create()))

    def test_an_equatable_subject_gets_an_equatable_view(self) -> None:
        """The promise itself, asserted as the enumeration of the paths that break it so that
        a failure names them instead of stopping at the first. It was an expected failure
        until the equatable view became a class of its own."""

        self.assertEqual(tuple(case.GetName() for case in _equatableSubjects() if not isinstance(case.Create().AsImmutable(), IEquatableTuple)), ())

    def test_an_equatable_view_is_allocated_exactly_when_it_is_not_the_subject_itself(self) -> None:
        """What replaced the perimeter bench this class used to carry.

        That one asserted the defect's extent — the type was missed exactly where the registry
        allocated — and it was written to fall when the fix landed. It did. The dichotomy it
        measured is still the useful one, read the other way round: a subject either answers
        with itself and allocates nothing, or hands out a view the registry allocated, never
        both. An allocation that produced the subject itself, or a self-answer that allocated
        on the way, would each be a leak this catches.

        Allocating is *not* the same as the subject being mutable: two of the five subjects
        are already immutable and allocate anyway. That is the optional optimisation of the
        design rule, applied to the reversed and hashable forms and not to the direct
        equatable ones — reported rather than asserted here, since asserting it would freeze
        the current state instead of the contract.
        """

        for case in _equatableSubjects():
            with self.subTest(type = case.GetName()):
                subject: _ITuple[Any] = case.Create()
                view: _ITuple[Any] = subject.AsImmutable()

                self.assertEqual(view is subject, not _allocatesAView(case.Create()))
                self.assertIsInstance(view, IEquatableTuple)

def _immutableViewSubjects() -> ReadOnlyArray[_CaseBase]:
    """Every case of the harness, plus the ordered set's tuple.

    That tuple is not in _ALL — it is not an indexable collection in its own right — but it is
    a subject of AsImmutable all the same, and it is where D-39 lived. A property that holds
    of every subject is enumerated over every subject, not over the ones that happen to be
    listed for other reasons.
    """

    return _ALL + (_Case("OrderedSetTuple", lambda: CreateOrderedSet(_createTuple()).AsTuple()),)

class TestImmutableViewContent(unittest.TestCase):
    """D-39: a subject's immutable view shows the subject's content.

    The ordered set's tuple delegated AsImmutable to its container instead of taking itself as
    the subject. On a reversed form that meant the view carried the direct order — (1, 2, 3)
    where the subject read (3, 2, 1) — silently, and out of reach of any type check: the
    declared return type was merely too wide, while the content was plainly wrong.

    Giving the class its own equatable view monitor fixed both at once, which is why this
    bench sits beside TestImmutableViewTyping rather than inside it. The type was the symptom;
    the subject was the cause, and a bench on the symptom would not have found it.

    Measured as local when it was found — one case in twenty-two — but the property is
    universal, so the enumeration is too.
    """

    def test_an_immutable_view_carries_the_content_of_its_subject(self) -> None:
        """One fresh collection per form: a view is memoised on first request, so reusing the
        subject would let the direct form's view answer for the reversed one's."""

        def assertCarries(subject: _ITuple[Any]) -> None:
            self.assertEqual(_snapshot(subject.AsImmutable()), _snapshot(subject))

        for case in _immutableViewSubjects():
            with self.subTest(type = case.GetName()):
                with self.subTest(form = "direct"):   assertCarries(case.Create())
                with self.subTest(form = "reversed"): assertCarries(case.Create().AsReversed())

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
        alive keeps the content it was given.

        The expected content is read from the source rather than from the slice. Reading the
        slice first is what fixes its content, so a copy that defers its read would pass
        either way — the order of the two reads is itself a coverage dimension here. The
        other direction is asserted by TestSliceIndependence.
        """

        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            key: slice = slice(0, 2)
            expected: ReadOnlyArray[int] = _snapshot(items)[key]
            view: ITuple[int] = items.AsImmutable()
            taken = view.SliceAt(key)

            case.Mutate(items)

            self.assertEqual(_snapshot(taken), expected)

        _subTests(self, subTest)

class TestSliceIndependence(unittest.TestCase):
    """A slice is an independent collection: neither side sees the other's writes.

    One direction is covered upstream. TestDerivedTransitivity asserts, over the seven types,
    that writing to the source leaves a slice taken beforehand alone — and it does reach each
    type's own SliceAt, the revocable view it slices through delegating straight to it. What
    that road cannot reach is the other direction: a view is read-only, so the slice it hands
    back has no write surface at all.

    The slice is therefore taken directly here, over the types whose slice can be written.
    That subset is computed rather than named, and its complement is asserted by the second
    bench: a list of names drifts, and in this module a subset by name meant an open defect
    until the last one was retired, so one written here would be misread as a defect marker
    instead of the structural fact it is.
    """

    def test_writing_through_a_slice_does_not_reach_the_source(self) -> None:
        """The direction the defect exhibited: ArrayCollection's slice held the parent's own
        cells, so the parent saw the write. The source is read before the slice is written,
        which is the only order that establishes anything, for the reason given on
        TestDerivedTransitivity.test_a_slice_taken_before_revocation_is_a_snapshot."""

        def subTest(case: _MutableCaseBase, items: IList[int]) -> None:
            taken: IArray[int] = items.SliceAt(slice(0, 2))
            untouched: ReadOnlyArray[int] = _snapshot(items)

            taken.SetAt(1, 77)

            self.assertEqual(_snapshot(items), untouched)

        _subTestsOf(self, _writableSlices(), subTest)

    def test_one_type_alone_slices_without_a_write_surface(self) -> None:
        """The counterpart of the subset above, and what allows it to stay implicit.

        SortedList is the one, on structural grounds rather than by defect: a sorted list
        cannot take an arbitrary positional write and stay sorted. A type that gains or loses
        a writable slice turns this red, so the subset cannot quietly widen.
        """

        written: ReadOnlyArray[str] = tuple(case.GetName() for case in _writableSlices())

        self.assertEqual(tuple(case.GetName() for case in _MUTABLE if case.GetName() not in written), ("SortedList",))

# The keys the conformance benches sweep, grouped by what each one reaches. A key set chosen
# for coverage is the substance of an index-translation bench, not its decoration: the
# ReverseKey defect was wrong on exactly the keys that reach the first element, and five
# hand-picked keys, all at step 1, had all passed before the sweep was widened.
_SLICE_KEYS: ReadOnlyArray[slice] = (
    slice(0, 2),             # an interior window
    slice(1, 4),             # one running past the end
    slice(1, 4, 2),          # a step above one
    slice(0, None, 2),       # a step above one, open-ended
    slice(None, None, None), # the whole thing, spelt as Python spells it
    slice(None, None, -1),   # descending, reaching index 0 — the case None exists for
    slice(4, 0, -1),         # descending, stopping short of index 0
    slice(-2, None),         # bounds counted from the end
    slice(3, 1),             # empty: start past stop
    slice(1, 1),             # empty: bounds coincide
    slice(9, 99))            # wholly out of range

def _orderPreservingSlices() -> ReadOnlyArray[_CaseBase]:
    """The cases whose slice keeps the order it was asked for, measured rather than named.

    A sorted collection slices into a sorted collection, so it cannot honour a descending
    key — and that is read off the returned type, not assumed from the name. The complement
    is asserted by TestSliceConformance.test_only_a_sorted_slice_reorders_its_content.
    """

    return tuple(case for case in _ALL if not isinstance(case.Create().SliceAt(slice(0, 2)), ISortedTuple))

class TestSliceConformance(unittest.TestCase):
    """SliceAt translates indices, and the reference for that translation is Python itself.

    Written for D-38, fixed in f035e0d: ReverseKey mirrored a slice's bounds and kept its
    step, which makes a descending slice with a positive step — empty. SliceAt on a
    reversed form returned nothing, on every type; assigning through a reversed slice raised
    IndexError; deleting through one silently removed nothing. None of it was covered. The
    slice benches above read the direct forms only, and the one type whose reversed slice
    would have been read recursed before reaching it, so the gap was held open by a second
    defect.

    These benches compare against `snapshot[key]` rather than against expected content. A
    table of expected results would have to be rewritten for every type and would encode one
    reading of the semantics; Python's own slicing *is* the semantics, and comparing against
    it is what makes a wrong translation visible instead of merely different.
    """

    def __Sweep(self, taken: Converter[_CaseBase, _ITuple[Any]]) -> None:
        for case in _orderPreservingSlices():
            with self.subTest(type = case.GetName()):
                items: _ITuple[Any] = taken(case)
                content: ReadOnlyArray[Any] = _snapshot(items)

                for key in _SLICE_KEYS:
                    with self.subTest(key = f"{key.start}:{key.stop}:{key.step}"):
                        self.assertEqual(_snapshot(items.SliceAt(key)), content[key])

    def test_a_slice_agrees_with_python(self) -> None:
        """The direct forms. Green before f035e0d as well — which is the point of having it:
        it is what establishes that the fix changed the reversed forms and nothing else."""

        self.__Sweep(lambda case: case.Create())

    def test_a_slice_of_a_reversed_form_agrees_with_python(self) -> None:
        """The reversed forms, which is what the defect emptied. Nine types, eleven keys, and
        the reversed form is reached through AsReversed() rather than built here: the defect
        was in the shared ReverseKey, so what matters is that every type's own reversed class
        goes through it."""

        self.__Sweep(lambda case: case.Create().AsReversed())

    def test_the_key_translation_agrees_with_python_over_its_domain(self) -> None:
        """The eleven keys above hold the *effects* of the translation on three elements;
        this holds the translation itself.

        Three elements are too few to separate a wrong formula from a right one: before
        f035e0d, one of the eleven keys passed by coincidence — [1:4:2] wanted (2,) and the
        broken formula happened to return (2,). And the formula that preceded the one in
        place was wrong on a bound the eleven keys never produce, which is how it passed five
        hand-picked cases before a sweep found it wrong on 1400 of 18432.

        So the domain is swept instead: every start and stop from -8 to 8 plus None, every
        step from -3 to 3 plus None, over lengths 0 to 6, against Python's own slicing of the
        reversed content. One collection per length, since ReverseKey reads only the count.
        """

        keys: ReadOnlyArray[slice] = tuple(slice(start, stop, step)
                                           for start in (None, *range(-8, 9))
                                           for stop in (None, *range(-8, 9))
                                           for step in (None, -3, -2, -1, 1, 2, 3))

        for length in range(0, 7):
            with self.subTest(length = length):
                items: _ITuple[int] = Tuple[int](tuple(range(1, length + 1)))
                reversed_: _ITuple[int] = items.AsReversed()
                content: ReadOnlyArray[int] = _snapshot(reversed_)
                wrong: list[str] = [f"[{key.start}:{key.stop}:{key.step}]"
                                    for key in keys if _snapshot(reversed_.SliceAt(key)) != content[key]]

                # The count and a sample, not the list: a failing sweep otherwise prints thousands of
                # keys and assertEqual truncates the message that names the scale.
                self.assertEqual(len(wrong), 0, f"{len(wrong)} of {len(keys)} keys disagree with Python at length {length}; first {', '.join(wrong[:5])}")

    def test_only_a_sorted_slice_reorders_its_content(self) -> None:
        """The complement of the subset above, and what lets it stay computed.

        SortedList is the one, on structural grounds and not by defect: its slice is itself a
        sorted collection, so a descending key comes back ascending. Asserted twice over —
        the name, so a type that gains or loses the property turns this red, and the content,
        so the exclusion states what the type *does* rather than only how it differs.
        """

        preserving: ReadOnlyArray[str] = tuple(case.GetName() for case in _orderPreservingSlices())
        reordering: ReadOnlyArray[str] = tuple(case.GetName() for case in _ALL if case.GetName() not in preserving)

        self.assertEqual(reordering, ("SortedList",))

        for case in _ALL:
            if case.GetName() in reordering:
                with self.subTest(type = case.GetName()):
                    taken: ReadOnlyArray[Any] = _snapshot(case.Create().SliceAt(slice(None, None, -1)))

                    self.assertEqual(taken, tuple(sorted(taken)))

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
        """Both cursor states are exercised, not only the advanced one.

        A cursor that has moved and one that never has are different states, and by this
        module's own rule the order of calls is a coverage dimension. No violation was found
        that separates them — a view's cursor dies of the view being revoked rather than
        through the enumerator registry, so removing that registration entirely leaves both
        states dying on all seven types. The second state is covered here rather than left
        to a named bench on one type, so that the absence of a separating violation stops
        being the reason anything is believed.
        """

        def subTest(case: _MutableCaseBase, items: _IList[int]) -> None:
            def exercise(source: _IList[int], advanced: bool) -> None:
                view: _ITuple[int] = source.AsImmutable()
                cursor: IEnumerator[int] = _assertIsNotNone(self, view.TryGetEnumerator())

                if advanced: self.assertTrue(cursor.MoveNext())

                case.Mutate(source)

                self.assertRaises(DiscardedError, cursor.MoveNext)

            # One collection per state: the first mutation would otherwise reach the second.
            with self.subTest(advanced = False): exercise(items, False)
            with self.subTest(advanced = True): exercise(cast(_IList[int], case.Create()), True)

        _subTests(self, subTest)

class TestEnumeratorInvalidation(unittest.TestCase):
    """F1': proof that the mechanism runs, not proof that it has not changed."""

    def test_an_active_enumerator_dies_on_mutation(self) -> None:
        def subTest(case: _MutableCaseBase, items: _IList[int]) -> None:
            enumerator: IEnumerator[int] = _assertIsNotNone(self, items.TryGetEnumerator())

            self.assertTrue(enumerator.MoveNext())

            case.Mutate(items)

            self.assertRaises(DiscardedError, enumerator.MoveNext)

        _subTests(self, subTest)

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

class TestSelectionStratum(unittest.TestCase):
    """The Selection stratum routes to its source's registry rather than keeping one.

    This class recorded D-8 for five passes: three types kept a registry of their own,
    and the two whose source is immutable carried a third status — the defect was
    established structurally but could not be exercised, so it sat under a skip.

    The defect was architectural, not local: the adapters inherited the registry
    ownership of a root collection, so they neither routed nor armed what they owned.
    Missing base classes were added and the three now route like the other two. The
    benches below are what is left of it — the conformance, asserted rather than the
    defect recorded.

    Two shapes are exercised, because the constructors take either road depending on
    what they are handed: a source that already satisfies the target interface is kept
    and routed to, one that does not is materialised and becomes the source itself.
    """

    def test_selection_list_routes_to_its_source_registry(self) -> None:
        """The road where the source is kept: a List already satisfies IList."""

        source: _IList[int] = _source()
        items: _IList[str] = SelectionList[int, str](source, Converters[int, str](str, int))

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_selection_equatable_tuple_routes_to_its_source_registry(self) -> None:
        source: IEquatableTuple[int] = _equatableSource()
        items: IEquatableTuple[str] = SelectionEquatableTuple[int, str](source, str)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_selection_hashable_tuple_routes_to_its_source_registry(self) -> None:
        source: IHashableTuple[int] = _hashableSource()
        items: IHashableTuple[str] = SelectionHashableTuple[int, str](source, str)

        self.assertIs(items.GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_an_incompatible_source_is_materialised_and_becomes_the_source(self) -> None:
        """The other road, stated positively — it used to sit here as a skip.

        A List does not satisfy IEquatableTuple, so it is materialised. What the wrapper
        then holds is the materialisation, and the object handed in is no longer its
        source: mutating it must leave both the content and the view untouched. The two
        clauses belong together. The surviving view alone would read as a revocation that
        failed to happen; paired with the unchanged content it says the opposite, which is
        that nothing happened to revoke.
        """

        source: _IList[int] = _source()
        items: IEquatableTuple[str] = SelectionEquatableTuple[int, str](cast(Any, source), str)
        content: ReadOnlyArray[str] = _snapshot(cast(ITuple[str], items))
        view: ITuple[str] = cast(_ITuple[str], items).AsImmutable()

        source.Add(9)
        gc.collect()

        self.assertEqual(_snapshot(cast(ITuple[str], items)), content)
        self.assertFalse(_revoked(view))
        self.assertEqual(_snapshot(view), content)

    def test_a_kept_source_that_can_change_revokes_through_the_converter(self) -> None:
        """The hardest case the correction has to hold, and the one that could not be
        built when the defect was being argued about.

        Exercising a missing route on the equatable stratum needs a source that is both
        an IEquatableTuple — so that it is kept rather than materialised — and able to
        change. A census found none: the concrete ones are tuple-backed, the circular one
        changes but takes no part in the mechanism, and the ordered set's tuple would have
        served but its only public entry recursed without end. That entry was repaired,
        so the case exists now.

        It is the sharpest check available on this stratum: the source is kept, it does
        change, and the view has to die. Keep it whatever else moves — it is the one bench
        standing between this stratum and a silent return of the defect.
        """

        items = CreateOrderedSet([1, 2, 3])
        source: IEquatableTuple[int] = items.AsTuple()
        converted: IEquatableTuple[str] = SelectionEquatableTuple[int, str](source, str)

        self.assertIs(converted.GetCollectionMonitors(), source.GetCollectionMonitors())

        view: ITuple[str] = cast(_ITuple[str], converted).AsImmutable()

        self.assertEqual(_snapshot(cast(ITuple[str], converted)), ("1", "2", "3"))

        items.Add(9)
        gc.collect()

        self.assertEqual(_snapshot(source), (1, 2, 3, 9), "the kept source is expected to change")
        self.assertTrue(_revoked(view))

    def test_mutating_the_source_revokes_a_selection_view(self) -> None:
        source: _IList[int] = _source()
        items: IList[str] = SelectionList[int, str](source, Converters[int, str](str, int))
        view: ITuple[str] = cast(_ITuple[str], items).AsImmutable()

        source.Add(9)

        self.assertTrue(_revoked(view))

    def test_mutating_the_selection_itself_revokes_its_view(self) -> None:
        items: IList[str] = SelectionList[int, str](_source(), Converters[int, str](str, int))
        view: ITuple[str] = cast(_ITuple[str], items).AsImmutable()

        items.Add("9")

        self.assertTrue(_revoked(view))

class TestProjectionGenerationIdentity(unittest.TestCase):
    """C2 by producer: a projection is a producer of views in its own right.

    The benches above establish identity and distinctness on root types. A projection sits
    one level below, and the failure mode it is exposed to is a registry shared upward or
    a deduplicator keyed on the root rather than on the producer — neither of which a
    sweep over roots can see.
    """

    def test_two_views_of_one_projection_are_the_same_instance(self) -> None:
        """S11. One producer, one generation — the producer here being the projection."""

        def project(_: _MutableCaseBase, __: IList[int], projection: ITupleBase[int], ___: ITuple[int]) -> None:
            self.assertIs(projection.AsImmutable(), projection.AsImmutable())

        _project(self, project)

    def test_a_source_and_its_reversal_yield_distinct_views_that_die_together(self) -> None:
        """S12, on the projection it names.

        Distinctness alone would be satisfied by a projection whose views are simply never
        registered — which is D-8's shape — so the death of both on one mutation is
        asserted in the same breath.
        """

        for case in _MUTABLE:
            with self.subTest(type = case.GetName()):
                items: IList[int] = cast(IList[int], case.Create())
                reversal: ITupleBase[int] = cast(ITupleBase[int], items.AsReversed())

                rootView: ITuple[int] = items.AsImmutable()
                reversedView: ITuple[int] = reversal.AsImmutable()

                self.assertIsNot(rootView, reversedView)
                self.assertFalse(_revoked(rootView))
                self.assertFalse(_revoked(reversedView))

                case.Mutate(items)

                self.assertTrue(_revoked(rootView))
                self.assertTrue(_revoked(reversedView))

    def test_a_projection_that_preserves_the_content_shares_the_view(self) -> None:
        """The other face of S12, and evidence for the sharing rule step 4 has to settle.

        S12 pairs a source with its reversal, which presents a different content. The two
        remaining projection forms do not: AsReadOnly and AsFixedSize narrow the write
        surface and leave the observable content identical. Measured here, both hand back
        the very instance the root hands back — which is the candidate rule of `4.1` §4.1,
        *one revocable per distinct observable content*, showing up as behaviour rather
        than as a proposal.

        Recorded as an observation, not endorsed as a contract: what step 4 has to decide
        is whether this is the rule or an accident of the current wiring. Either way, a
        change here should be deliberate, and this bench is what makes it visible.
        """

        shared: tuple[str, ...] = ("AsReadOnly", "AsFixedSize")

        for case in _MUTABLE:
            items = cast(IList[int], case.Create())

            for name, projection in _projections(items):
                if name not in shared: continue

                with self.subTest(type = case.GetName(), projection = name):
                    self.assertIsNot(projection, items)
                    self.assertIs(cast(ITupleBase[int], projection).AsImmutable(), items.AsImmutable())

class TestConversionStratum(unittest.TestCase):
    """S10 and C7 across a conversion.

    Every derivation the benches above exercise keeps the element type: reversal changes
    the order, read-only and fixed-size narrow the write surface. A converter changes what
    the elements *are*, and it is the one form where the registration could plausibly stop
    at the adapter — the adapter holds a container of TIn and presents TOut, so it has a
    reason of its own to own a registry.
    """

    def test_mutating_the_inner_source_revokes_a_view_on_the_converter(self) -> None:
        """S10 proper: the registration reaches the root across the conversion."""

        source: _IList[int] = _source()
        items: _ConvertingTuple = _ConvertingTuple(cast(Any, source))
        view: ITuple[str] = items.AsImmutable()

        self.assertEqual(_snapshot(cast(ITuple[Any], view)), ("1", "2", "3"))

        source.Add(9)
        gc.collect()

        self.assertTrue(_revoked(view))

    def test_the_converter_routes_to_the_registry_of_its_source(self) -> None:
        """C7 read on the wiring rather than on the effect, so that a pass that revokes for
        the wrong reason does not read as conformant."""

        source: _IList[int] = _source()

        self.assertIs(_ConvertingTuple(cast(Any, source)).GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_the_converting_list_routes_to_the_registry_of_its_source(self) -> None:
        """Where D-8 actually lived, and where it was fixed.

        The dossier characterised D-8 on `Abstraction.Selection`. It was not theirs: the
        converting *list* of `Abstract.Collection` kept a registry of its own while the
        converting *tuple* beside it routed, and Selection inherited the gap rather than
        introducing it. The correction landed here, by supplying the base classes the
        hierarchy was missing.
        """

        source: _IList[int] = _source()

        self.assertIs(_ConvertingList(cast(Any, source)).GetCollectionMonitors(), source.GetCollectionMonitors())

    def test_mutating_the_inner_source_revokes_a_view_on_the_converting_list(self) -> None:
        """The behavioural face of the bench above. It is the one that matters: routing
        is the mechanism, revocation is what the consumer sees."""

        source: _IList[int] = _source()
        view: ITuple[str] = _ConvertingList(cast(Any, source)).AsImmutable()

        source.Add(9)
        gc.collect()

        self.assertTrue(_revoked(view))

class TestStatusCarriesTheCause(unittest.TestCase):
    """G11', the half that belongs to this chantier.

    The original G11 asked for two distinct enumerator substitutions and that the registry
    path take the second. No enumerator substitution exists any more — the whole
    `IInvalidatable*Enumerator` family was removed and the cause now travels through an
    iteration status — so the invariant was reformulated on the correspondence table.

    The mapping half of that table already lives in `Tests/Collections/Enumeration.py`,
    asserted on a synthetic status, `Faulted` included. What no synthetic status can show
    is that a real revocation reaches `Revoked` at all, and that is precisely what G11
    guarded: a path that keeps taking the old route by inertia compiles, passes, and never
    raises. So what is asserted here is the path, not the mapping.

    `Faulted` is absent by decision, not by omission: producing a genuine fault of the
    iteration body calls for a synthetic enumerator, which is the other module's business
    and where it is already covered.
    """

    def __GetStates(self) -> dict[str, tuple[IterationResult, type[InvalidOperationError]|None]]:
        return {"idle":        (IterationResult.Idle,        None),
                "completed":   (IterationResult.Completed,   None),
                "stopped":     (IterationResult.Stopped,     InvalidOperationError),
                "invalidated": (IterationResult.Invalidated, InvalidatedError),
                "revoked":     (IterationResult.Revoked,     InvalidatedError)}

    def __Build(self, state: str) -> IEnumerator[int]:
        items: _IList[int] = _source()

        match state:
            case "idle":
                return _assertIsNotNone(self, items.TryGetEnumerator())

            case "completed":
                enumerator: IEnumerator[int] = _assertIsNotNone(self, items.TryGetEnumerator())

                while enumerator.MoveNext(): pass

                return enumerator

            case "stopped":
                enumerator = _assertIsNotNone(self, items.TryGetEnumerator())

                enumerator.MoveNext()
                enumerator.Stop()

                return enumerator

            case "invalidated":
                enumerator = _assertIsNotNone(self, items.TryGetEnumerator())

                enumerator.MoveNext()
                items.Add(9)

                return enumerator

            case "revoked":
                cursor: IEnumerator[int] = _assertIsNotNone(self, items.AsImmutable().TryGetEnumerator())

                cursor.MoveNext()
                items.Add(9)

                return cursor

            case _: raise AssertionError(state)

    def test_the_table_holds_on_every_state(self) -> None:
        """Five states, reached through real collections rather than declared."""

        for state, (result, errorType) in self.__GetStates().items():
            with self.subTest(state = state):
                enumerator: IEnumerator[int] = self.__Build(state)

                gc.collect()

                status = enumerator.GetStatus()
                error = status.TryGetIterationError()

                self.assertEqual(status.GetResult(), result)

                if errorType is None: self.assertIsNone(error)
                else: self.assertIs(type(error), errorType)

    def test_revocation_does_not_fall_back_on_the_generic_error(self) -> None:
        """The clause G11 existed for.

        A revoked cursor and an invalidated enumerator must both name the cause, and a
        consumer must not have to tell them apart. Landing on a bare InvalidOperationError
        — what a path taking the old route by inertia would produce — is the failure this
        rules out, and `assertIs` on the type is what rules it out: InvalidatedError is
        itself an InvalidOperationError, so an isinstance check would accept the bug.
        """

        for state in ("invalidated", "revoked"):
            with self.subTest(state = state):
                error = self.__Build(state).GetStatus().TryGetIterationError()

                self.assertIs(type(error), InvalidatedError)
                self.assertIsInstance(error, DiscardedError)

class TestProtocolReversal(unittest.TestCase):
    """reverse() reverses, on every type that offers the door.

    The mutator table above measures the named API only; the protocol face was measured
    nowhere outside the ordered set's own module, which is how a reversal that silently
    did nothing survived a whole commit. That was D-55, found here and closed: this class
    is what keeps it closed. The door is AsMutableSequence(), so the types that decline
    it -- a sorted list, any fixed-size array -- are absent here by their own lattice
    position rather than by an exclusion, per 5.30.
    """

    def __GetSubjects(self) -> ReadOnlyArray[tuple[str, Any]]:
        """The instances to reverse.

        The conversion stratum is added by hand: it is the one type in this module that
        offers the door without sitting in the registry table, and it is one of the two
        the hook left behind when it was introduced.
        """

        subjects: list[tuple[str, Any]] = [(case.GetName(), case.Create()) for case in _MUTABLE]

        subjects.append(("ConvertingList", _ConvertingList(_source())))

        return tuple((name, items) for name, items in subjects if callable(getattr(items, "AsMutableSequence", None)))

    @staticmethod
    def __Reverse(items: Any) -> tuple[ReadOnlyArray[Any], ReadOnlyArray[Any]]:
        before: ReadOnlyArray[Any] = _snapshot(cast(_ITuple[Any], items))

        items.AsMutableSequence().reverse()

        return before, _snapshot(cast(_ITuple[Any], items))

    def test_the_reversal_reverses(self) -> None:
        subjects: ReadOnlyArray[tuple[str, Any]] = self.__GetSubjects()

        self.assertGreaterEqual(len(subjects), 4, "the reversal perimeter has emptied; this bench would prove nothing")

        for name, items in subjects:
            with self.subTest(case = name):
                before, after = self.__Reverse(items)

                self.assertEqual(after, tuple(reversed(before)),
                                 f"{name}.reverse() left the order unchanged" if after == before else f"{name}.reverse() produced {after}")

# ---------------------------------------------------------------------------
# The non-vacuity control, domiciled
# ---------------------------------------------------------------------------
# `2.5` §10 recorded that this control had no home: rebuilt at every pass, living outside
# the repository, reproducible only as far as a report described it. The C4 counter in
# TestLazyCreation is the counter-example it also carried — a check that the instrument
# bites, kept in the tree. This is that model applied to the harness as a whole.

# A floor, deliberately, not the figure. Measured on f26e751: the four witnesses shed 162
# assertions, and the whole suite 242 over 13 methods. An equality would be a magic number
# that churns with every type added to the tables above, and would be repaired by raising
# it — which is the one repair that destroys the control.
_NON_VACUITY_FLOOR: int = 100

@contextlib.contextmanager
def _breakingRevocation() -> Generator[None]:
    """Rebuilds D-28 for the length of the block.

    The defect: the revocation cookie overrode `_DisposeOverride` without calling
    `super()`, so the substitution installing the throwing value provider never happened
    and the view went on reading through to a live source. The replacement drops the
    `super()` call and keeps everything else the override does, so what is rebuilt is
    D-28 and not a blanket no-op.

    This is the second and last place in this module that reaches past the public API;
    like `_counting()` it is confined here and restored on the way out. The substitution
    is a class attribute, hence global while it is installed: the control is sound only
    on a single-threaded run, which is how the suite runs.
    """

    cookieType: Any = _cookieType()
    original: Any = cookieType._DisposeOverride

    def broken(self: Any, reason: DiscardReason) -> None:
        # The private attribute is resolved by suffix rather than spelled out. Spelling it out
        # worked until a generic nested class was added to the cookie: under CPython 3.12 a
        # nested *generic* class makes the rest of the enclosing body mangle private names
        # with the nested class's name instead of the enclosing one, so the spelled-out name
        # silently became wrong and this control stopped reconstructing the defect. 3.13 fixes
        # the mangling and is now the floor, but the technique has no reason to depend on it.
        attributes: dict[str, Any] = cast(dict[str, Any], vars(self))
        name: str = next(key for key in attributes.keys() if key.endswith("__onDisposed"))

        getattr(self, name)(reason)

    cookieType._DisposeOverride = broken

    try: yield
    finally: cookieType._DisposeOverride = original

def _runBenches(benches: ReadOnlyArray[tuple[type[unittest.TestCase], str]]) -> unittest.TestResult:
    """Runs the named benches through a real result object.

    Calling a bench method directly would work — `subTest` is a passthrough with no active
    outcome — but only the first failing assertion would surface, and that behaviour is an
    implementation detail of unittest. A suite and a result are the public API, count every
    sub-test that falls, and keep the per-bench attribution the control is built on.
    """

    result: unittest.TestResult = unittest.TestResult()

    unittest.TestSuite(benchType(name) for benchType, name in benches).run(result)

    return result

def _fallen(result: unittest.TestResult) -> int:
    """Assertions that fell. Errors count with failures: an artificial state may produce
    either — D-33 turned one into the other without changing the total — and the control
    has no reason to distinguish them."""

    return len(result.failures) + len(result.errors)

def _fellIn(result: unittest.TestResult, name: str) -> bool:
    """Whether a named bench is among those that fell. A sub-test reports as _SubTest; the
    bench that owns it is reachable through test_case."""

    return any(getattr(getattr(test, "test_case", test), "_testMethodName", None) == name
               for test, _ in result.failures + result.errors)

class TestHarnessNonVacuity(unittest.TestCase):
    """A green harness is worth nothing unless it can go red.

    Rather than assert a count, which would churn, this names the benches that must fall
    and checks each one: four invariants, four distinct ways of falling. This class is
    never among them, which is what keeps the control from running itself.
    """

    def __GetWitnesses(self) -> ReadOnlyArray[tuple[type[unittest.TestCase], str]]:
        return ((TestWritePathCoverage, "test_every_mutator_revokes"),               # C5
                (TestRevocationIsTotal, "test_every_read_path_raises"),              # D1
                (TestGenerationIdentity, "test_generations_chain"),                  # C3
                (TestSourceRelease, "test_a_revoked_view_does_not_pin_its_source"))  # D5

    def test_the_rebuilt_defect_is_a_violation(self) -> None:
        """`2.5` §7, paid for with a false positive: establish that the violation is one
        before concluding anything from what it makes fall. A violation that leaves the
        harness green proves nothing about the harness.

        Two clauses, because D-28 has two faces. The view keeps answering; and it keeps
        answering while its own cookie already reports itself discarded — the substitution
        of the cookie lives in the private body, out of reach of the override, so H8 holds
        and the divergence is exactly the gap D-28 opens.
        """

        with _breakingRevocation():
            items: _IList[int] = _source()
            view: _ITuple[int] = items.AsImmutable()

            items.Add(9)
            gc.collect()

            self.assertFalse(_revoked(view), "D-28 rebuilt, yet the view still refuses to read")
            self.assertIn("revoked", view.ToString().lower(),
                          "the cookie should report itself discarded while the view still answers")

        restored: _IList[int] = _source()
        survivor: _ITuple[int] = restored.AsImmutable()

        restored.Add(9)
        gc.collect()

        self.assertTrue(_revoked(survivor), "the seam was not restored on the way out")

    def test_the_named_benches_fall_on_it(self) -> None:
        """Both halves are asserted. Green on an intact seam is what makes the fall
        attributable to the violation rather than to something already broken."""

        witnesses: ReadOnlyArray[tuple[type[unittest.TestCase], str]] = self.__GetWitnesses()
        intact: unittest.TestResult = _runBenches(witnesses)

        self.assertEqual(_fallen(intact), 0, "the witnesses are expected to pass on an intact seam")

        with _breakingRevocation(): broken: unittest.TestResult = _runBenches(witnesses)

        for benchType, name in witnesses:
            with self.subTest(bench = f"{benchType.__name__}.{name}"):
                self.assertTrue(_fellIn(broken, name), f"{benchType.__name__}.{name} did not fall on the rebuilt defect")

        self.assertGreater(_fallen(broken), _NON_VACUITY_FLOOR,
                           f"only {_fallen(broken)} assertions fell; the control is losing its grip")

if __name__ == "__main__": unittest.main()