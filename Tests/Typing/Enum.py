"""
Unit tests for WinCopies.Typing.Enum module.
"""

import unittest

from collections.abc import Iterable
from typing import cast, Any

from WinCopies.Typing.Enum import TypedEnumProtocol, IntEnum, UnorderedIntEnum, StrEnum, IntFlag

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

if __name__ == '__main__': unittest.main()