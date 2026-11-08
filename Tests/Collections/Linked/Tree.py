"""
Unit tests for the trees (WinCopies.Collections.Linked.Tree)
"""

import unittest

from collections.abc import Callable, Iterable
from typing import Any, cast
from unittest import mock

import WinCopies.Collections.Linked.Tree as TreeModule

from WinCopies.Collections import ReadOnlyArray
from WinCopies.Collections.Enumeration.Core import IEnumerator
from WinCopies.Collections.Linked.Tree import ITree, Tree, TreeBase

_BUILDS: ReadOnlyArray[tuple[str, Iterable[int]|None, ReadOnlyArray[int]]] = (
    ("no argument", None, ()),
    ("an empty source", (), ()),
    ("one item", (1,), (1,)),
    ("three items", (1, 2, 3), (1, 2, 3)))
"""The ways of building a tree, with the items it holds at its top level once built."""

class TestATreeIsBuiltWithItsItems(unittest.TestCase):
    """D-121. From 30cf3815 until 4c162b77, a tree could not be built at all: Tree() raised
    AttributeError. Since 30cf3815, the initializer of the welded list base asks for the node
    cookie, which TreeBase created only after calling it. No bench built a tree, and nothing else in
    the framework builds one."""

    def __build(self, items: Iterable[int]|None) -> ITree[int]:
        try: return Tree[int]() if items is None else Tree[int](items)
        except Exception as error: raise self.failureException(f"building a tree raised {type(error).__name__}: {error}") from error

    def __assertReads(self, tree: ITree[int], expected: ReadOnlyArray[int], name: str) -> None:
        self.assertEqual(tuple(tree.AsIterable()), expected, f"built with {name}, the tree reads another sequence")

        enumerator: IEnumerator[int]|None = tree.TryGetEnumerator()
        enumerated: list[int] = []

        if enumerator is not None:
            while enumerator.TryMoveNext(): enumerated.append(enumerator.GetCurrent())

        self.assertEqual(tuple(enumerated), expected, f"built with {name}, the tree's enumerator reads another sequence")

    def test_a_tree_holds_the_items_it_is_built_with(self) -> None:
        for name, items, expected in _BUILDS:
            with self.subTest(build = name): self.__assertReads(self.__build(items), expected, name)

    def test_a_tree_takes_items_after_it_is_built(self) -> None:
        for name, items, expected in _BUILDS:
            with self.subTest(build = name):
                tree: ITree[int] = self.__build(items)

                for value in (7, 8): tree.AddLast(value)

                self.__assertReads(tree, expected + (7, 8), name)

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheTreeBenchesCanFail(unittest.TestCase):
    """The benches above, run against the code as it stood before their fix: green on the intact
    tree, red on the rebuilt one. A class is reached through its public name, and is the one that
    carries the attribute rebuilt."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, target: Any, rebuilt: dict[str, Any]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with mock.patch.multiple(target, **rebuilt): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")

    def test_the_construction_benches_fall_when_the_cookie_follows_the_base_initializer(self) -> None:
        """As from 30cf3815 until 4c162b77 (D-121): TreeBase.__init__ created its node cookie after
        the initializer of its base, which reads it since 30cf3815. Rebuilt in that order; the
        private classes of the module are reached by name."""

        cookieProvider: Any = getattr(TreeModule, "_CookieProvider")
        recursiveUpdater: Any = getattr(TreeModule, "_RecursiveUpdater")
        nodeRecursiveUpdater: Any = getattr(TreeModule, "_NodeRecursiveUpdater")

        def cookieLast(self: Any, items: Iterable[Any]|None = None) -> None:
            def setter(name: str) -> Callable[[Any], None]: return lambda func: setattr(self, name, func)

            super(TreeBase, cast(TreeBase[Any, Any], self)).__init__(items)

            setattr(self, "_TreeBase__cookie", cookieProvider(self))
            setattr(self, "_TreeBase__recursive", recursiveUpdater(self, setter("_TreeBase__recursive")))
            setattr(self, "_TreeBase__nodeRecursive", nodeRecursiveUpdater(self, setter("_TreeBase__nodeRecursive")))

        for name in ("test_a_tree_holds_the_items_it_is_built_with", "test_a_tree_takes_items_after_it_is_built"):
            with self.subTest(bench = name): self.__assertFalls(TestATreeIsBuiltWithItsItems, name, TreeBase, {"__init__": cookieLast})

if __name__ == '__main__': unittest.main()
