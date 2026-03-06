"""
Unit tests for WinCopies.Enum module.
"""

import unittest

from enum import Enum, Flag

from WinCopies.Enum import (
    IsMemberOf, EnsureMemberOf,
    IsValueOf, EnsureValueOf,
    IsFieldOf, EnsureFieldOf,
    ToKeyValuePair, ToKeyValuePairs,
    ToTuple, ToTuples,
    IsIn, EnsureIn,
    TryGetMember, TryGetName, TryGetValue,
    TryGetField, TryGetFieldFromName, TryGetFieldFromValue,
    HasFlag, EnsureHasFlag,
    EnumerateNames, EnumerateValues,
    EnumerateFieldNames, EnumerateFieldValues,
    Print
)
from WinCopies.Typing.Pairing import KeyValuePair

class Color(Enum):
    Red = 1
    Green = 2
    Blue = 3

class Permission(Flag):
    Read = 1
    Write = 2
    Execute = 4

class TestIsMemberOf(unittest.TestCase):
    """Tests for IsMemberOf and EnsureMemberOf."""

    def test_member_exists(self) -> None:
        """IsMemberOf returns True for valid member names."""
        self.assertTrue(IsMemberOf(Color, "Red"))
        self.assertTrue(IsMemberOf(Color, "Green"))
        self.assertTrue(IsMemberOf(Color, "Blue"))

    def test_member_not_exists(self) -> None:
        """IsMemberOf returns False for unknown or wrong-case names."""
        self.assertFalse(IsMemberOf(Color, "Yellow"))
        self.assertFalse(IsMemberOf(Color, "red"))  # Case-sensitive

    def test_not_an_enum_raises_assertion(self) -> None:
        """IsMemberOf raises AssertionError if the type is not an enum."""
        with self.assertRaises(AssertionError):
            IsMemberOf(int, "x") # type: ignore

    def test_ensure_member_exists(self) -> None:
        """EnsureMemberOf does not raise for a valid member name."""
        EnsureMemberOf(Color, "Red")

    def test_ensure_member_not_exists_raises(self) -> None:
        """EnsureMemberOf raises ValueError for an unknown member name."""
        with self.assertRaises(ValueError):
            EnsureMemberOf(Color, "Yellow")

class TestIsValueOf(unittest.TestCase):
    """Tests for IsValueOf and EnsureValueOf."""

    def test_value_exists(self) -> None:
        """IsValueOf returns True for valid enum values."""
        self.assertTrue(IsValueOf(Color, 1))
        self.assertTrue(IsValueOf(Color, 2))
        self.assertTrue(IsValueOf(Color, 3))

    def test_value_not_exists(self) -> None:
        """IsValueOf returns False for values absent from the enum."""
        self.assertFalse(IsValueOf(Color, 0))
        self.assertFalse(IsValueOf(Color, 99))

    def test_not_an_enum_raises_assertion(self) -> None:
        """IsValueOf raises AssertionError if the type is not an enum."""
        with self.assertRaises(AssertionError):
            IsValueOf(str, 1) # type: ignore

    def test_ensure_value_exists(self) -> None:
        """EnsureValueOf does not raise for a valid enum value."""
        EnsureValueOf(Color, 1)

    def test_ensure_value_not_exists_raises(self) -> None:
        """EnsureValueOf raises ValueError for an absent value."""
        with self.assertRaises(ValueError):
            EnsureValueOf(Color, 99)

class TestIsFieldOf(unittest.TestCase):
    """Tests for IsFieldOf and EnsureFieldOf."""

    def test_field_belongs_to_its_own_enum(self) -> None:
        """IsFieldOf returns True when e is the same enum type as the field."""
        self.assertTrue(IsFieldOf(Color, Color.Red))
        self.assertTrue(IsFieldOf(Color, Color.Blue))

    def test_field_wrong_enum_type_raises_assertion(self) -> None:
        """IsFieldOf raises AssertionError when e is not a subclass of type(f)."""
        with self.assertRaises(AssertionError):
            IsFieldOf(Permission, Color.Red)

    def test_ensure_field_belongs(self) -> None:
        """EnsureFieldOf does not raise when the field belongs to the enum."""
        EnsureFieldOf(Color, Color.Green)

    def test_ensure_field_wrong_type_raises_assertion(self) -> None:
        """EnsureFieldOf propagates the AssertionError from IsFieldOf on type mismatch."""
        with self.assertRaises(AssertionError):
            EnsureFieldOf(Permission, Color.Red)

class TestConversion(unittest.TestCase):
    """Tests for ToKeyValuePair, ToKeyValuePairs, ToTuple, ToTuples."""

    def test_to_key_value_pair(self) -> None:
        """ToKeyValuePair converts an enum member to a KeyValuePair(name, value)."""
        kvp = ToKeyValuePair(Color.Red)

        self.assertEqual(kvp.GetKey(), "Red")
        self.assertEqual(kvp.GetValue(), 1)

    def test_to_key_value_pair_all_members(self) -> None:
        """ToKeyValuePair works correctly for every member of the enum."""
        self.assertEqual(ToKeyValuePair(Color.Green).GetKey(), "Green")
        self.assertEqual(ToKeyValuePair(Color.Green).GetValue(), 2)
        self.assertEqual(ToKeyValuePair(Color.Blue).GetKey(), "Blue")
        self.assertEqual(ToKeyValuePair(Color.Blue).GetValue(), 3)

    def test_to_key_value_pairs_count(self) -> None:
        """ToKeyValuePairs yields exactly one pair per enum member."""
        self.assertEqual(len(list(ToKeyValuePairs(Color))), 3)

    def test_to_key_value_pairs_order(self) -> None:
        """ToKeyValuePairs yields pairs in enum declaration order."""
        pairs = list(ToKeyValuePairs(Color))

        self.assertEqual(pairs[0].GetKey(), "Red")
        self.assertEqual(pairs[0].GetValue(), 1)
        self.assertEqual(pairs[1].GetKey(), "Green")
        self.assertEqual(pairs[1].GetValue(), 2)
        self.assertEqual(pairs[2].GetKey(), "Blue")
        self.assertEqual(pairs[2].GetValue(), 3)

    def test_to_tuple(self) -> None:
        """ToTuple converts an enum member to a (name, value) tuple."""
        self.assertEqual(ToTuple(Color.Red), ("Red", 1))
        self.assertEqual(ToTuple(Color.Green), ("Green", 2))
        self.assertEqual(ToTuple(Color.Blue), ("Blue", 3))

    def test_to_tuples(self) -> None:
        """ToTuples yields a (name, value) tuple for each enum member in order."""
        self.assertEqual(
            list(ToTuples(Color)),
            [("Red", 1), ("Green", 2), ("Blue", 3)])

class TestIsIn(unittest.TestCase):
    """Tests for IsIn and EnsureIn."""

    def test_is_in_valid_tuple(self) -> None:
        """IsIn returns True for a matching (name, value) tuple."""
        self.assertTrue(IsIn(Color, ("Red", 1)))
        self.assertTrue(IsIn(Color, ("Blue", 3)))

    def test_is_in_tuple_wrong_value(self) -> None:
        """IsIn returns False when the value does not match the name."""
        self.assertFalse(IsIn(Color, ("Red", 2)))

    def test_is_in_tuple_unknown_name(self) -> None:
        """IsIn returns False for a name absent from the enum."""
        self.assertFalse(IsIn(Color, ("Yellow", 1)))

    def test_is_in_valid_kvp(self) -> None:
        """IsIn returns True for a matching IKeyValuePair."""
        self.assertTrue(IsIn(Color, KeyValuePair("Green", 2)))

    def test_is_in_invalid_kvp(self) -> None:
        """IsIn returns False for an IKeyValuePair with a wrong value."""
        self.assertFalse(IsIn(Color, KeyValuePair("Green", 99)))

    def test_not_an_enum_raises_assertion(self) -> None:
        """IsIn raises AssertionError if the type is not an enum."""
        with self.assertRaises(AssertionError):
            IsIn(list, ("x", 1)) # type: ignore

    def test_ensure_in_valid_tuple(self) -> None:
        """EnsureIn does not raise for a valid entry."""
        EnsureIn(Color, ("Red", 1))

    def test_ensure_in_invalid_raises(self) -> None:
        """EnsureIn raises ValueError for an entry absent from the enum."""
        with self.assertRaises(ValueError):
            EnsureIn(Color, ("Red", 99))

class TestTryGet(unittest.TestCase):
    """Tests for TryGetMember, TryGetName, TryGetValue, TryGetField,
    TryGetFieldFromName, and TryGetFieldFromValue."""

    def test_try_get_member_found(self) -> None:
        """TryGetMember returns the selected value when the predicate matches."""
        result = TryGetMember(Color, lambda o: o.value == 2, lambda o: o.name)

        self.assertEqual(result, "Green")

    def test_try_get_member_not_found(self) -> None:
        """TryGetMember returns None when no member satisfies the predicate."""
        result = TryGetMember(Color, lambda o: o.value == 99, lambda o: o.name)

        self.assertIsNone(result)

    def test_try_get_member_not_an_enum_raises(self) -> None:
        """TryGetMember raises AssertionError if the type is not an enum."""
        with self.assertRaises(AssertionError):
            TryGetMember(int, lambda _: True, lambda o: o) # type: ignore

    def test_try_get_name_found(self) -> None:
        """TryGetName returns the name corresponding to a valid value."""
        self.assertEqual(TryGetName(Color, 1), "Red")
        self.assertEqual(TryGetName(Color, 3), "Blue")

    def test_try_get_name_not_found(self) -> None:
        """TryGetName returns None for a value absent from the enum."""
        self.assertIsNone(TryGetName(Color, 99))

    def test_try_get_value_found(self) -> None:
        """TryGetValue returns the integer value corresponding to a valid name."""
        self.assertEqual(TryGetValue(Color, "Red"), 1)
        self.assertEqual(TryGetValue(Color, "Blue"), 3)

    def test_try_get_value_not_found(self) -> None:
        """TryGetValue returns None for a name absent from the enum."""
        self.assertIsNone(TryGetValue(Color, "Yellow"))

    def test_try_get_field_found(self) -> None:
        """TryGetField returns the first member matching the predicate."""
        result = TryGetField(Color, lambda o: o.value > 1)

        self.assertEqual(result, Color.Green)

    def test_try_get_field_not_found(self) -> None:
        """TryGetField returns None when no member satisfies the predicate."""
        self.assertIsNone(TryGetField(Color, lambda o: o.value > 100))

    def test_try_get_field_from_name_found(self) -> None:
        """TryGetFieldFromName returns the member with the matching name."""
        self.assertIs(TryGetFieldFromName(Color, "Green"), Color.Green)

    def test_try_get_field_from_name_not_found(self) -> None:
        """TryGetFieldFromName returns None for an unknown name."""
        self.assertIsNone(TryGetFieldFromName(Color, "Yellow"))

    def test_try_get_field_from_value_found(self) -> None:
        """TryGetFieldFromValue returns the member with the matching value."""
        self.assertIs(TryGetFieldFromValue(Color, 2), Color.Green)

    def test_try_get_field_from_value_not_found(self) -> None:
        """TryGetFieldFromValue returns None for an absent value."""
        self.assertIsNone(TryGetFieldFromValue(Color, 99))

class TestFlag(unittest.TestCase):
    """Tests for HasFlag, EnsureHasFlag, EnumerateFieldNames, EnumerateFieldValues, and Print."""

    def test_has_flag_true(self) -> None:
        """HasFlag returns True for each flag set in the combined value."""
        perm = Permission.Read | Permission.Write

        self.assertTrue(HasFlag(perm, Permission.Read))
        self.assertTrue(HasFlag(perm, Permission.Write))

    def test_has_flag_false(self) -> None:
        """HasFlag returns False for a flag absent from the combined value."""
        self.assertFalse(HasFlag(Permission.Read, Permission.Write))
        self.assertFalse(HasFlag(Permission.Read, Permission.Execute))

    def test_has_flag_single(self) -> None:
        """HasFlag returns True when the value is a single matching flag."""
        self.assertTrue(HasFlag(Permission.Execute, Permission.Execute))

    def test_ensure_has_flag_succeeds(self) -> None:
        """EnsureHasFlag does not raise when the flag is set."""
        perm = Permission.Read | Permission.Execute

        EnsureHasFlag(perm, Permission.Read)
        EnsureHasFlag(perm, Permission.Execute)

    def test_ensure_has_flag_raises(self) -> None:
        """EnsureHasFlag raises ValueError when the flag is absent."""
        with self.assertRaises(ValueError):
            EnsureHasFlag(Permission.Read, Permission.Write)

    def test_enumerate_field_names_combined(self) -> None:
        """EnumerateFieldNames yields the name of each active flag."""
        perm = Permission.Read | Permission.Write
        names = list(EnumerateFieldNames(perm))

        self.assertIn("Read", names)
        self.assertIn("Write", names)
        self.assertNotIn("Execute", names)

    def test_enumerate_field_names_single(self) -> None:
        """EnumerateFieldNames yields a single name for a single flag."""
        names = list(EnumerateFieldNames(Permission.Execute))

        self.assertEqual(names, ["Execute"])

    def test_enumerate_field_values_combined(self) -> None:
        """EnumerateFieldValues yields the integer value of each active flag."""
        perm = Permission.Read | Permission.Execute
        values = list(EnumerateFieldValues(perm))

        self.assertIn(1, values)   # Read
        self.assertIn(4, values)   # Execute
        self.assertNotIn(2, values)  # Write

    def test_enumerate_field_values_single(self) -> None:
        """EnumerateFieldValues yields a single value for a single flag."""
        self.assertEqual(list(EnumerateFieldValues(Permission.Write)), [2])

    def test_print_single_flag(self) -> None:
        """Print returns just the flag name for a single flag."""
        self.assertEqual(Print(Permission.Read), "Read")

    def test_print_multiple_flags(self) -> None:
        """Print returns a comma-separated string of active flag names."""
        result = Print(Permission.Read | Permission.Write)

        self.assertIn("Read", result)
        self.assertIn("Write", result)
        self.assertIn(",", result)

class TestEnumerate(unittest.TestCase):
    """Tests for EnumerateNames and EnumerateValues."""

    def test_enumerate_names_order(self) -> None:
        """EnumerateNames yields names in enum declaration order."""
        self.assertEqual(list(EnumerateNames(Color)), ["Red", "Green", "Blue"])

    def test_enumerate_names_count(self) -> None:
        """EnumerateNames yields exactly one name per member."""
        self.assertEqual(len(list(EnumerateNames(Color))), 3)

    def test_enumerate_values_order(self) -> None:
        """EnumerateValues yields values in enum declaration order."""
        self.assertEqual(list(EnumerateValues(Color)), [1, 2, 3])

    def test_enumerate_values_count(self) -> None:
        """EnumerateValues yields exactly one value per member."""
        self.assertEqual(len(list(EnumerateValues(Color))), 3)

if __name__ == '__main__':
    unittest.main()