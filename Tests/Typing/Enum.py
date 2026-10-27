"""
Unit tests for WinCopies.Typing.Enum module.
"""

import collections.abc
import contextlib
import gc
import typing
import unittest

from collections.abc import Generator, Iterable
from typing import cast, Any, Callable
from unittest import mock

from WinCopies.Typing.Enum import (TypedEnumProtocol, IntEnum, UnorderedIntEnum, StrEnum, IntFlag,
                                   TypedEnumBase, TypedEnum, TypedFlag, EquatableEnum, EquatableFlag, OrderedEnum)

class Priority(IntEnum):
    Low = 1
    High = 2

class Level(IntEnum):
    Low = 1

class Code(UnorderedIntEnum):
    A = 1
    B = 2

class Permission(IntFlag):
    Read = 1
    Write = 2

class Name(StrEnum):
    A = "a"
    B = "b"

class TestEquality(unittest.TestCase):
    def test_member_equals_itself(self) -> None:
        enums: Iterable[TypedEnumProtocol] = (Priority.Low, Code.A, Permission.Read, Name.A)

        for member in enums:
            with self.subTest(member=member): self.assertTrue(member == member)

        for member in enums: self.assertTrue(member.Equals(cast(Any, member)))

    def test_members_with_different_values_differ(self) -> None:
        self.assertTrue(Priority.Low != Priority.High) # pyright: ignore[reportUnnecessaryComparison]
        self.assertFalse(Priority.Low.Equals(Priority.High))

    def test_member_does_not_equal_its_raw_value(self) -> None:
        def assertNotEqual(x: TypedEnumProtocol|int|str, y: int|str|TypedEnumProtocol) -> None:
            self.assertFalse(x == y)

        for member, value in ((Priority.Low, 1), (Code.A, 1), (Permission.Read, 1), (Name.A, "a")):
            with self.subTest(member=member):
                assertNotEqual(member, value)
                assertNotEqual(value, member)

                self.assertTrue(member != value)

    def test_members_of_different_enums_with_equal_values_differ(self) -> None:
        self.assertFalse(Priority.Low == Level.Low) # pyright: ignore[reportUnnecessaryComparison]
        self.assertTrue(Priority.Low != Level.Low) # pyright: ignore[reportUnnecessaryComparison]

class TestHashing(unittest.TestCase):
    def test_equal_members_have_equal_hashes(self) -> None:
        self.assertEqual(hash(Priority.Low), hash(Priority(1)))

    def test_set_keeps_members_and_raw_values_apart(self) -> None:
        self.assertEqual(len({1, Priority.Low, Level.Low}), 3)
        self.assertEqual(len({Priority.Low, Level.Low, 1}), 3)

    def test_dictionary_lookup_by_raw_value_misses(self) -> None:
        values: dict[object, str] = {Priority.Low: "low"}

        self.assertIsNone(values.get(1))

class TestOrdering(unittest.TestCase):
    def test_members_of_same_enum_are_ordered(self) -> None:
        self.assertTrue(Priority.Low < Priority.High)
        self.assertTrue(Priority.Low <= Priority.Low)
        self.assertTrue(Priority.High > Priority.Low)
        self.assertTrue(Priority.High >= Priority.High)
        self.assertEqual(sorted((Priority.High, Priority.Low)), [Priority.Low, Priority.High])

    def test_compare_to(self) -> None:
        self.assertIsNone(Priority.Low.CompareTo(Priority.Low))
        self.assertTrue(Priority.High.CompareTo(Priority.Low))
        self.assertIs(Priority.Low.CompareTo(Priority.High), False)
        self.assertTrue(Priority.Low.IsLessThan(Priority.High))
        self.assertTrue(Priority.Low.IsLessThanOrEqual(Priority.Low))
        self.assertTrue(Priority.High.IsGreaterThan(Priority.Low))
        self.assertTrue(Priority.High.IsGreaterThanOrEqual(Priority.High))

    def test_ordering_against_raw_value_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            _ = Priority.Low < 2 # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    def test_ordering_against_other_enum_raises_type_error(self) -> None:
        with self.assertRaises(TypeError):
            _ = Priority.Low < Level.Low # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

    def test_equatable_only_enums_are_not_ordered(self) -> None:
        with self.assertRaises(TypeError):
            _ = Code.A < Code.B # type: ignore[operator] # pyright: ignore[reportOperatorIssue]
        with self.assertRaises(TypeError):
            _ = Permission.Read < Permission.Write # type: ignore[operator] # pyright: ignore[reportOperatorIssue]
        with self.assertRaises(TypeError):
            _ = Name.A < Name.B # type: ignore[operator] # pyright: ignore[reportOperatorIssue]

class TestUnorderedIntEnum(unittest.TestCase):
    def test_subclass_with_members_can_be_defined(self) -> None:
        self.assertEqual(list(Code), [Code.A, Code.B])
        self.assertIs(Code(1), Code.A)

    def test_non_integer_value_is_rejected(self) -> None:
        with self.assertRaisesRegex(TypeError, "value 'a' is not an instance of int"):
            class _Invalid(UnorderedIntEnum): # pyright: ignore[reportUnusedClass]
                A = "a" # pyright: ignore[reportArgumentType]

def _answer(ask: Callable[[], bool]) -> bool|BaseException:
    """What an ABC answers, or what it raises instead."""

    try: return ask()
    except Exception as error: return error

def _matchesIterable(value: object) -> bool:
    match value:
        case Iterable(): return True
        case _: return False

def _asksAbout(name: str, value: object) -> tuple[tuple[str, Callable[[], bool]], ...]:
    """The three ways of asking Iterable about one value."""

    return ((f"isinstance({name}, Iterable)",        lambda: isinstance(value, Iterable)),
            (f"isinstance({name}, typing.Iterable)", lambda: isinstance(value, typing.Iterable)),
            (f"match {name} with case Iterable()",   lambda: _matchesIterable(value)))

def _metaclassesAmong(base: type) -> list[str]:
    """The metaclasses, classes that derive from type, among the subclasses of base, at any depth."""

    found: list[str] = []
    seen: set[type] = set()
    pending: list[type] = [base]

    while pending:
        for subclass in type.__subclasses__(pending.pop()):
            if subclass in seen: continue

            seen.add(subclass)
            pending.append(subclass)

            if issubclass(subclass, type): found.append(f"{subclass.__module__}.{subclass.__qualname__}")

    return found

class TestTheEnumMetaclassLeavesTheAbstractBaseClassesAlone(unittest.TestCase):
    """D-115, its first half. The metaclass of the typed enumerations derived from Iterable, and so stood among the
    subclasses of that ABC. Asked about an object that has no __iter__, an ABC walks its subclasses and asks each for its
    own; a metaclass, which derives from type, finds there the unbound type.__subclasses__ and raises. So once
    WinCopies.Typing.Enum was imported, isinstance(x, Iterable) raised TypeError for every object x that is not iterable,
    in the whole process, whoever asked. No bench put a non-iterable object to an ABC."""

    def test_an_abstract_base_class_answers_for_an_object_it_does_not_describe(self) -> None:
        asks: tuple[tuple[str, Callable[[], bool]], ...] = (("issubclass(int, Iterable)", lambda: issubclass(cast(type, int), Iterable)),
                                                            *_asksAbout("None", None), *_asksAbout("5", 5), *_asksAbout("object()", object()))

        for ask, answer in asks:
            with self.subTest(ask = ask): self.assertIs(_answer(answer), False, f"{ask} does not answer False")

    def test_no_metaclass_stands_among_the_subclasses_of_an_abstract_base_class(self) -> None:
        """The cause, asserted on every ABC of collections.abc rather than on Iterable alone: a metaclass deriving from any
        of them breaks that one the same way. The walk sees the classes that the process has created."""

        for name in cast(list[str], getattr(collections.abc, "__all__")):
            base: object = getattr(collections.abc, name)

            if isinstance(base, type):
                with self.subTest(abc = name): self.assertEqual(_metaclassesAmong(base), [], f"a metaclass derives from {name}")

class TestOnlyAnEnumerationIterates(unittest.TestCase):
    """D-115, its second half. Deriving from Iterable also handed the classes that the metaclass makes without EnumMeta,
    TypedEnum, EquatableEnum and the other bases, which have no member, the __iter__ of Iterable, which yields nothing:
    iterating one answered an empty enumeration instead of refusing, and so did Enumerate(TypedEnum). The type checkers
    still see these classes as iterable, so that the functions typed Type[TypedEnum[T]] may iterate the enumeration they
    are given; at runtime, an enumeration iterates through EnumMeta."""

    def test_a_class_that_is_no_enumeration_refuses_to_be_iterated(self) -> None:
        for base in (TypedEnumBase, TypedEnum, TypedFlag, EquatableEnum, EquatableFlag, OrderedEnum):
            with self.subTest(base = base.__qualname__):
                with self.assertRaises(TypeError, msg = f"{base.__qualname__} iterates although it has no member"): iter(base)

                self.assertFalse(isinstance(cast(object, base), Iterable), f"{base.__qualname__} claims to be iterable")

    def test_an_enumeration_iterates_its_members(self) -> None:
        enumerations: tuple[tuple[type, list[object]], ...] = (
            (Priority,   [Priority.Low, Priority.High]),
            (Code,       [Code.A, Code.B]),
            (Permission, [Permission.Read, Permission.Write]),
            (Name,       [Name.A, Name.B]),
            (IntEnum,    []))

        for enumeration, members in enumerations:
            with self.subTest(enumeration = enumeration.__qualname__):
                self.assertEqual(list(cast(Iterable[object], enumeration)), members, f"{enumeration.__qualname__} iterates other members")
                self.assertTrue(isinstance(cast(object, enumeration), Iterable), f"{enumeration.__qualname__} does not claim to be iterable")

@contextlib.contextmanager
def _aMetaclassDerivingFromIterable() -> Generator[None]:
    """The metaclass as it was declared until D-115 was closed, under another name: its existence alone puts a metaclass
    among the subclasses of Iterable. The caches of Iterable are cleared once it exists, since the defect was there before
    any question was put to the ABC, and an answer the ABC cached earlier would hide it. It is deleted and collected on the
    way out, which takes it out of the subclasses again; that is checked, since the rest of the suite would otherwise run
    with the defect."""

    class _EnumTypeBaseAsBefore(type, Iterable[Any]): pass

    Iterable._abc_caches_clear() # type: ignore[attr-defined] # pyright: ignore[reportAttributeAccessIssue]

    try: yield
    finally:
        del _EnumTypeBaseAsBefore

        gc.collect()

        if _metaclassesAmong(Iterable): raise RuntimeError("the rebuilt metaclass outlived its control")

def _run(bench: type[unittest.TestCase], name: str) -> unittest.TestResult:
    result: unittest.TestResult = unittest.TestResult()

    bench(name).run(result)

    return result

class TestTheEnumMetaclassBenchesCanFail(unittest.TestCase):
    """The benches of D-115, run against the metaclass as it was declared before: green on the intact tree, red on the
    rebuilt one, and red on their assertions rather than on an error. The first half is rebuilt by a metaclass deriving from
    Iterable, which is what the defect was; the second by the __iter__ of Iterable, set on the metaclass of TypedEnum,
    reached through the class, as the metaclass inherited it."""

    def __assertFalls(self, bench: type[unittest.TestCase], name: str, rebuilding: Callable[[], contextlib.AbstractContextManager[Any]]) -> None:
        self.assertTrue(_run(bench, name).wasSuccessful(), f"{name} is expected to pass on the intact tree")

        with rebuilding(): broken: unittest.TestResult = _run(bench, name)

        self.assertFalse(broken.wasSuccessful(), f"{name} did not fall on the rebuilt defect")
        self.assertEqual(broken.errors, [], f"{name} fell on an error rather than on its assertions")

    def test_the_abstract_base_class_benches_fall_when_a_metaclass_derives_from_iterable(self) -> None:
        for name in ("test_an_abstract_base_class_answers_for_an_object_it_does_not_describe", "test_no_metaclass_stands_among_the_subclasses_of_an_abstract_base_class"):
            with self.subTest(bench = name): self.__assertFalls(TestTheEnumMetaclassLeavesTheAbstractBaseClassesAlone, name, _aMetaclassDerivingFromIterable)

    def test_the_iteration_bench_falls_when_the_metaclass_inherits_the_iter_of_iterable(self) -> None:
        self.__assertFalls(TestOnlyAnEnumerationIterates, "test_a_class_that_is_no_enumeration_refuses_to_be_iterated",
                           lambda: mock.patch.multiple(type(TypedEnum), create = True, __iter__ = vars(Iterable)["__iter__"]))

if __name__ == '__main__': unittest.main()