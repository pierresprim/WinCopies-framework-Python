"""
Benches of the iteration contexts (WinCopies.Collections.Enumeration: GetIterationContext,
TryGetIterationContext, and the contexts that the enumerables of the framework give), within which
every loop of the framework over a collection of the framework runs (Enumeration 7.1 and
Enumeration 7.2).

A loop of the framework gets its context from GetIterationContext and iterates over AsIterator()
within a with statement. The exit of that statement stops the enumerator of a collection of the
framework, so that it leaves the registry of its collection at once, even when the loop is left early
or by an exception. A collection backed by a Python container or generator gives a context over it,
without building an enumerator. An iterator that the caller passes stays to the caller: its context
neither closes nor stops it. Only a generator that its owner created for the iteration is closed, when
the owner asks for it through disposeGenerator, as GeneratorBase and IteratorProvider do. None and an
empty collection give an empty context.

The benches iterate over real collections, and read whether an enumerator is still started and
whether a generator ran its finally clause. Every generator that a bench closes, or must not close,
is kept referenced, so that only an explicit close runs its finally clause, and not the garbage
collector. They count no call of an internal method.
"""

import unittest

from collections.abc import Callable, Generator as SystemGenerator, Iterable
from typing import Any, cast
from unittest import mock

import WinCopies.Collections.Enumeration as Contexts
import WinCopies.Collections.Iteration as Iteration
import WinCopies.Collections.Iteration.Enumeration as IterationEnumeration

from WinCopies.Collections import Generator as _Generator
from WinCopies.Collections.Abstraction.Collection import CreateList
from WinCopies.Collections.Abstraction.Mapping import Dictionary
from WinCopies.Collections.Enumeration import IIterationContext
from WinCopies.Collections.Enumeration.Core import IEnumerable, IEnumerator, IEnumeratorBase, Enumerable, Generator, GeneratorBase, IteratorProvider, AsEnumerable, CreateCountableIterable, CreateEnumeratorProvider, CreateIteratorProvider, GetEmptyEnumerable

class _Generation:
    """A generator over the given items, which records whether it ran its finally clause: its closing
    runs it, and so does its end."""

    def __init__(self, items: Iterable[int]) -> None:
        self.closed: bool = False
        self.generator: _Generator[int] = self.__generate(items)

    def __generate(self, items: Iterable[int]) -> _Generator[int]:
        try: yield from items
        finally: self.closed = True

class _Numbers(Generator[int]):
    """A Generator whose _TryGetIterator creates a new recording generator for each iteration, and
    keeps every one of them."""

    def __init__(self) -> None:
        super().__init__()

        self.generations: list[_Generation] = []

    def _TryGetIterator(self) -> _Generator[int]:
        generation: _Generation = _Generation((1, 2, 3))

        self.generations.append(generation)

        return generation.generator

    def IsResumable(self) -> bool|None: return True
class _NoNumbers(GeneratorBase[int]):
    """A GeneratorBase whose _TryGetIterator gives no generator."""

    def __init__(self) -> None: super().__init__()

    def _TryGetIterator(self) -> _Generator[int]|None: return None

    def IsResumable(self) -> bool|None: return True

def _recorded(items: Iterable[int]) -> tuple[Enumerable[int], list[IEnumerator[int]]]:
    """A collection of the framework, seen through an enumerable that records every enumerator it
    gives, so that a bench can read whether that enumerator is still started."""

    source: IEnumerable[int] = CreateList(list(items))
    enumerators: list[IEnumerator[int]] = []

    def provide() -> IEnumerator[int]:
        enumerator: IEnumerator[int] = source.GetEnumerator()

        enumerators.append(enumerator)

        return enumerator

    return (CreateEnumeratorProvider(provide), enumerators)

def _firstThenExit(context: IIterationContext[int]) -> int|None:
    """Leaves the loop over the context after its first item, and answers that item."""

    with context:
        for item in context.AsIterator(): return item

    return None

class TestTheExitStopsTheEnumeratorOfACollection(unittest.TestCase):
    """Enumeration 7.1. A for loop does not stop the enumerator that it gets from a collection of the
    framework when it is left early, and the enumerator then stays registered, so that every write to
    the collection pays for its invalidation. The exit of the with statement stops it."""

    def test_an_early_exit_stops_the_enumerator(self) -> None:
        context: IIterationContext[int] = Contexts.GetIterationContext(CreateList([1, 2, 3]))

        self.assertEqual(_firstThenExit(context), 1)

        if not isinstance(context, IEnumerator): self.fail("a collection of the framework does not give its enumerator as its context")

        self.assertFalse(context.IsStarted(), "the enumerator is still started after an early exit")

    def test_an_exception_in_the_loop_stops_the_enumerator(self) -> None:
        context: IIterationContext[int] = Contexts.GetIterationContext(CreateList([1, 2, 3]))

        with self.assertRaises(ValueError):
            with context:
                for _ in context.AsIterator(): raise ValueError()

        if not isinstance(context, IEnumerator): self.fail("a collection of the framework does not give its enumerator as its context")

        self.assertFalse(context.IsStarted(), "the enumerator is still started after an exception")

class TestACollectionBackedByAPythonContainerBuildsNoEnumerator(unittest.TestCase):
    """Enumeration 7.2 §4. Wrapping the iterator of a Python container in an enumerator of the
    framework cost about 4.5 µs per item, for an enumerator that has no registry to leave. Such a
    collection now gives a context over its container or its generator, and its items are the same."""

    def test_the_context_is_no_enumerator_and_gives_the_items(self) -> None:
        dictionary: Dictionary[int, int] = Dictionary[int, int]({1: 1, 2: 2, 3: 3})

        cases: tuple[tuple[str, IEnumerable[int], list[int]], ...] = (
            ("a countable iterable",           CreateCountableIterable((1, 2, 3)),              [1, 2, 3]),
            ("an iterable over a Python list", AsEnumerable([1, 2, 3]),                         [1, 2, 3]),
            ("an iterator provider",           CreateIteratorProvider(lambda: iter((1, 2, 3))), [1, 2, 3]),
            ("the keys of a dictionary",       dictionary.GetKeys(),                            [1, 2, 3]),
            ("the values of a dictionary",     dictionary.GetValues(),                          [1, 2, 3]),
            ("a generator",                    _Numbers(),                                      [1, 2, 3]),
            ("a generator without generator",  _NoNumbers(),                                    []),
            ("the empty enumerable",           GetEmptyEnumerable(),                            []))

        for name, enumerable, expected in cases:
            with self.subTest(enumerable = name):
                context: IIterationContext[int] = Contexts.GetIterationContext(enumerable)

                with context: self.assertEqual(list(context.AsIterator()), expected)

                self.assertNotIsInstance(context, IEnumerator, "the context is an enumerator")

class TestAnIteratorThatTheCallerPassesStaysToTheCaller(unittest.TestCase):
    """Enumeration 7.1 and Enumeration 7.2 §6. The context of an iterator that the caller passes
    neither closes nor stops it: the caller can go on reading it, as after a for loop. The first draft
    of the closing of generators closed every generator, and lost what Traversal.Iterate and GetFirst
    read after the first item."""

    def test_a_generator_is_not_closed(self) -> None:
        generation: _Generation = _Generation((1, 2, 3))

        _firstThenExit(Contexts.GetIterationContext(generation.generator))

        self.assertFalse(generation.closed, "the generator was closed")
        self.assertEqual(list(generation.generator), [2, 3], "the rest of the generator is lost")

    def test_an_iterator_is_not_closed(self) -> None:
        iterator = iter([1, 2, 3])

        _firstThenExit(Contexts.GetIterationContext(iterator))

        self.assertEqual(list(iterator), [2, 3], "the rest of the iterator is lost")

    def test_an_enumerator_is_not_stopped(self) -> None:
        enumerator: IEnumerator[int] = CreateList([1, 2, 3]).GetEnumerator()

        _firstThenExit(Contexts.GetIterationContext(enumerator.AsIterator()))

        self.assertTrue(enumerator.IsStarted(), "the enumerator was stopped")
        self.assertEqual(list(enumerator.AsIterator()), [2, 3], "the rest of the enumerator is lost")

class TestNoneAndAnEmptyCollectionGiveAnEmptyContext(unittest.TestCase):
    """Enumeration 7.2 §2. None gives the empty context of the Enumeration package, for which
    TryGetIterationContext answers None, and an empty collection gives no item."""

    def test_none_and_empty_collections_give_no_item(self) -> None:
        cases: tuple[tuple[str, IEnumerable[int]|Iterable[int]|None], ...] = (("None", None), ("an empty list of the framework", CreateList(list[int]())), ("an empty Python list", list[int]()))

        for name, items in cases:
            with self.subTest(items = name):
                context: IIterationContext[int] = Contexts.GetIterationContext(items)

                with context: self.assertEqual(list(context.AsIterator()), [])

    def test_try_answers_none_for_none(self) -> None:
        self.assertIsNone(Contexts.TryGetIterationContext(cast(Iterable[int]|None, None)), "TryGetIterationContext gives a context for None")

class TestDisposeGeneratorClosesOnlyAGenerator(unittest.TestCase):
    """Enumeration 7.2 §6. With disposeGenerator, the exit closes a generator, which runs its finally
    clauses and the exits of its own with statements. It closes nothing else: an iterator that is not
    a generator stays to the caller, and a collection of the framework gives its own context."""

    def test_a_generator_is_closed(self) -> None:
        for name, get in (("GetIterationContext", Contexts.GetIterationContext), ("TryGetIterationContext", Contexts.TryGetIterationContext)):
            with self.subTest(function = name):
                generation: _Generation = _Generation((1, 2, 3))
                context: IIterationContext[int]|None = get(generation.generator, True)

                if context is None: self.fail(f"{name} gives no context for a generator")

                _firstThenExit(context)

                self.assertTrue(generation.closed, "the generator was not closed")
                self.assertEqual(list(generation.generator), [])

    def test_an_iterator_that_is_no_generator_is_not_closed(self) -> None:
        iterator = iter([1, 2, 3])

        _firstThenExit(Contexts.GetIterationContext(iterator, True))

        self.assertEqual(list(iterator), [2, 3], "the rest of the iterator is lost")

    def test_an_enumerator_is_not_stopped(self) -> None:
        enumerator: IEnumerator[int] = CreateList([1, 2, 3]).GetEnumerator()

        _firstThenExit(Contexts.GetIterationContext(enumerator.AsIterator(), True))

        self.assertTrue(enumerator.IsStarted(), "the enumerator was stopped")

    def test_a_collection_gives_its_own_context(self) -> None:
        context: IIterationContext[int] = Contexts.GetIterationContext(CreateList([1, 2, 3]), True)

        _firstThenExit(context)

        if not isinstance(context, IEnumerator): self.fail("a collection of the framework does not give its enumerator as its context")

        self.assertFalse(context.IsStarted(), "the enumerator is still started after an early exit")

class TestTheEnumerablesCloseTheGeneratorThatTheyCreate(unittest.TestCase):
    """Enumeration 7.2 §6, ae1d3cce. GeneratorBase and IteratorProvider create a generator for each
    iteration, which belongs to the iteration: their context closes it at the exit. A new iteration
    gets a new generator."""

    def test_an_iterator_provider_closes_its_generator(self) -> None:
        generations: list[_Generation] = []

        def provide() -> _Generator[int]:
            generation: _Generation = _Generation((1, 2, 3))

            generations.append(generation)

            return generation.generator

        provider: IEnumerable[int] = CreateIteratorProvider(provide)

        self.assertEqual(_firstThenExit(Contexts.GetIterationContext(provider)), 1)
        self.assertTrue(generations[0].closed, "the generator of the iterator provider was not closed")

        context: IIterationContext[int] = Contexts.GetIterationContext(provider)

        with context: self.assertEqual(list(context.AsIterator()), [1, 2, 3], "a new iteration does not get a new generator")

    def test_a_generator_enumerable_closes_its_generator(self) -> None:
        numbers: _Numbers = _Numbers()

        self.assertEqual(_firstThenExit(Contexts.GetIterationContext(numbers)), 1)
        self.assertTrue(numbers.generations[0].closed, "the generator of the Generator was not closed")

        context: IIterationContext[int] = Contexts.GetIterationContext(numbers)

        with context: self.assertEqual(list(context.AsIterator()), [1, 2, 3], "a new iteration does not get a new generator")

class TestAnAbandonedLazyFunctionStopsItsEnumerator(unittest.TestCase):
    """Enumeration 7.1 §2 and daa87084. A lazy function of the framework holds the with statement
    inside its generator, so that closing the generator, which raises GeneratorExit at its yield,
    stops the enumerator that it iterates over."""

    def test_closing_the_generator_stops_the_enumerator(self) -> None:
        functions: tuple[tuple[str, Callable[[Enumerable[int]], SystemGenerator[int]]], ...] = (
            ("IncludeWhile", lambda items: Iteration.IncludeWhile(items, lambda item: True)),
            ("AppendItem",   lambda items: Iteration.AppendItem(items, 0)),
            ("Concatenate",  lambda items: Iteration.Concatenate((items,))),
            ("ExcludeUntil", lambda items: IterationEnumeration.ExcludeUntil(items, lambda item: True)))

        for name, function in functions:
            with self.subTest(function = name):
                items, enumerators = _recorded((1, 2, 3))
                generator: SystemGenerator[int] = function(items)

                self.assertEqual(next(generator), 1)

                generator.close()

                self.assertEqual(len(enumerators), 1)
                self.assertFalse(enumerators[0].IsStarted(), "the enumerator is still started once the generator is closed")

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

def _contextAsBeforeD74b40c6(items: Any, disposeGenerator: bool = False) -> Any:
    """The dispatch before d74b40c6: every enumerable gave its enumerator."""

    if isinstance(items, IEnumerable): return items.GetEnumerator() # pyright: ignore[reportUnknownVariableType]

    return getattr(Contexts, "_IterationContext")(items)

def _contextClosingEveryGenerator(items: Any, disposeGenerator: bool = False) -> Any:
    """The first draft of ae1d3cce: every generator, passed or created, was closed at the exit."""

    if isinstance(items, Contexts.IEnumerable): return items.GetIterationContext() # pyright: ignore[reportUnknownVariableType]

    return getattr(Contexts, "_GenerationContext" if isinstance(items, SystemGenerator) else "_IterationContext")(items)

def _includeWhileAsAt22f4f550(items: Any, predicate: Any) -> Any:
    """IncludeWhile before daa87084, without a with statement."""

    for item in Iteration.TryEnumerate(items):
        if predicate(item): yield item
        else: break

def _contextAsAtD74b40c6(self: Any) -> Any:
    """The context of GeneratorBase and IteratorProvider at d74b40c6, before they asked for the
    closing of their generator."""

    iterator: Iterable[Any] = self._TryGetIterator()

    return Contexts.GetIterationContext(iterator)

def _exitThatDoesNothing(self: Any, excType: Any, exc: Any, traceback: Any) -> Any: return None

class TestTheIterationContextBenchesCanFail(unittest.TestCase):
    """Each bench of this file run against the code as it stood before the commit that made it pass,
    or against a likely defect: green on the intact tree, red on the rebuilt one. Each function or
    method is replaced where its callers look it up."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_stop_benches_fall_when_the_exit_does_not_stop_the_enumerator(self) -> None:
        """A likely defect: an exit that does not stop the enumerator, as a for loop."""

        for name in ("test_an_early_exit_stops_the_enumerator", "test_an_exception_in_the_loop_stops_the_enumerator"):
            with self.subTest(bench = name): self.__assertFalls(TestTheExitStopsTheEnumeratorOfACollection, name, IEnumeratorBase, {"_OnExiting": _exitThatDoesNothing})

        self.__assertFalls(TestAnAbandonedLazyFunctionStopsItsEnumerator, "test_closing_the_generator_stops_the_enumerator", IEnumeratorBase, {"_OnExiting": _exitThatDoesNothing})

    def test_the_container_bench_falls_as_it_stood_before_d74b40c6(self) -> None:
        self.__assertFalls(TestACollectionBackedByAPythonContainerBuildsNoEnumerator, "test_the_context_is_no_enumerator_and_gives_the_items", Contexts, {"_GetIterationContext": _contextAsBeforeD74b40c6})

    def test_the_generator_bench_falls_when_every_generator_is_closed(self) -> None:
        self.__assertFalls(TestAnIteratorThatTheCallerPassesStaysToTheCaller, "test_a_generator_is_not_closed", Contexts, {"_GetIterationContext": _contextClosingEveryGenerator})

    def test_the_none_bench_falls_when_try_gives_a_context_for_none(self) -> None:
        """A likely defect: TryGetIterationContext behaving as GetIterationContext."""

        self.__assertFalls(TestNoneAndAnEmptyCollectionGiveAnEmptyContext, "test_try_answers_none_for_none", Contexts, {"TryGetIterationContext": Contexts.GetIterationContext})

    def test_the_closing_bench_falls_when_the_generation_context_does_not_close(self) -> None:
        self.__assertFalls(TestDisposeGeneratorClosesOnlyAGenerator, "test_a_generator_is_closed", getattr(Contexts, "_GenerationContext"), {"_OnExiting": _exitThatDoesNothing})

    def test_the_benches_of_the_enumerables_fall_as_they_stood_at_d74b40c6(self) -> None:
        for name, target in (("test_an_iterator_provider_closes_its_generator", IteratorProvider), ("test_a_generator_enumerable_closes_its_generator", GeneratorBase)):
            with self.subTest(bench = name): self.__assertFalls(TestTheEnumerablesCloseTheGeneratorThatTheyCreate, name, target, {"GetIterationContext": _contextAsAtD74b40c6})

    def test_the_lazy_bench_falls_as_it_stood_before_daa87084(self) -> None:
        self.__assertFalls(TestAnAbandonedLazyFunctionStopsItsEnumerator, "test_closing_the_generator_stops_the_enumerator", Iteration, {"IncludeWhile": _includeWhileAsAt22f4f550})